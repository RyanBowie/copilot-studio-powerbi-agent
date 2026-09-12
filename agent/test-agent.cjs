// Built-in SDK body logging is suppressed in this process; diagnostics below never log headers or rows.
process.env.DEBUG = '';
const { execFileSync } = require('node:child_process');
const { createHash, randomBytes } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { CopilotStudioClient, ConnectionSettings, getCopilotStudioConnectionUrl } = require('@microsoft/agents-copilotstudio-client');

const DEFAULT_PROMPT = 'What tables and measures are in this model?';
const COMPONENTS = ['ModelMetadata', 'GeneratedDaxQuery', 'GeneratedDaxAdvice', 'GeneratedQueryError',
  'VerifyCallerSchemaVisibility', 'ExecuteGeneratedQuery'];

function resolvePrompt(args) {
  const index = args.indexOf('--prompt');
  if (index < 0) return DEFAULT_PROMPT;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error('--prompt requires a value.');
  return value;
}

function scrub(text) {
  return String(text).replace(/Bearer\s+\S+/gi, 'Bearer [omitted]')
    .replace(/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, '[token omitted]')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[account omitted]')
    .replace(/https?:\/\/\S+/g, '[URL omitted]');
}

function safeRoute(value) {
  const url = new URL(typeof value === 'string' ? value : value.url || String(value));
  return url.origin + url.pathname + (url.searchParams.has('api-version') ? '?api-version=' + url.searchParams.get('api-version') : '');
}

function textFacts(text = '') {
  return {
    characters: text.length,
    topicFallback: /not able to find a related topic|no related topic/i.test(text),
    connectionRequired: /connection manager|verify your credentials|get you connected|ConnectionReferenceNotFound/i.test(text),
    unexecutedLabel: /NOT EXECUTED|UNEXECUTED/.test(text),
    envelopeMentioned: /__kind/.test(text) && /__status/.test(text),
    metadataMentioned: /snapshot|prepared|schema/i.test(text)
  };
}

function diagnosticHints(value, output = [], depth = 0) {
  if (!value || typeof value !== 'object' || depth > 8) return output;
  if (Array.isArray(value)) {
    value.slice(0, 40).forEach(v => diagnosticHints(v, output, depth + 1));
    return output;
  }
  for (const [key, item] of Object.entries(value)) {
    if (/^(text|content|body|rows|result|results|outputs|response)$/i.test(key)) continue;
    if (/^(topicName|dialogName|dialogId|dialog|schemaName|actionName|actionId|toolName|id)$/i.test(key) && typeof item === 'string') {
      const match = COMPONENTS.find(name => item === name || item.endsWith('.' + name));
      if (match) output.push({ field: key, component: match });
    } else if (/^(tableExpression|query|generatedDax)$/i.test(key) && typeof item === 'string') {
      output.push({ field: key, characters: item.length, sha256: createHash('sha256').update(item).digest('hex') });
    } else if (typeof item === 'object') diagnosticHints(item, output, depth + 1);
  }
  return output;
}

function activityFacts(activity) {
  const facts = {
    type: activity.type, channelId: activity.channelId || null,
    name: typeof activity.name === 'string' ? scrub(activity.name).slice(0, 100) : null,
    fields: Object.keys(activity), text: textFacts(activity.text),
    attachmentTypes: (activity.attachments || []).map(a => a.contentType),
    // Hints are not proof of execution; result/row/text contents are deliberately excluded.
    structuredHints: ['event', 'trace', 'invoke', 'invokeResponse'].includes(activity.type)
      ? diagnosticHints(activity.value || activity.channelData) : []
  };
  function inspectCards(value) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value)) return value.forEach(inspectCards);
    for (const [key, item] of Object.entries(value)) {
      if ((key === 'text' || key === 'title') && typeof item === 'string') {
        facts.text.connectionRequired ||= textFacts(item).connectionRequired;
      } else if (typeof item === 'object') inspectCards(item);
    }
  }
  inspectCards(activity.attachments);
  return facts;
}

function tokenFacts(token, config) {
  try {
    const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    const scopes = String(claims.scp || '').split(' ').filter(Boolean);
    return {
      tenantMatchesConfiguration: claims.tid === config.tenantId,
      audience: claims.aud,
      copilotScopes: scopes.filter(s => /CopilotStudio|Copilots/i.test(s)),
      hasInvokeScope: scopes.includes('CopilotStudio.Copilots.Invoke'),
      hasTestScope: scopes.includes('CopilotStudio.Copilots.Test')
    };
  } catch {
    return { claimsNotInspected: true };
  }
}

async function runProbe(options = {}) {
  const args = options.args || process.argv.slice(2);
  const config = options.config || require('./resources.json');
  const prompt = resolvePrompt(args); // Shared by BOTH SDK and evaluation routes.
  const log = options.log || console.log;
  const token = options.token || execFileSync(process.env.ComSpec || 'cmd.exe', [
    '/d', '/s', '/c',
    `az account get-access-token --resource https://api.powerplatform.com --tenant ${config.tenantId} --query accessToken -o tsv`
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  const evidence = {
    routeKind: args.includes('--maker-test') ? 'evaluation-json' : 'published-sdk-sse',
    intendedPrompt: prompt, agentId: config.agentId, schemaName: config.schemaName,
    token: tokenFacts(token, config), http: [], startActivities: [], turnActivities: [],
    freshConversation: true, turnSent: false, chatEndToEndPass: false
  };
  log('Probe:', JSON.stringify({ routeKind: evidence.routeKind, intendedPrompt: prompt, token: evidence.token }));
  const originalFetch = globalThis.fetch;
  const fetchImpl = options.fetchImpl || originalFetch;
  const diagnosticFetch = async (url, init = {}) => {
    const call = { method: init.method || 'GET', route: safeRoute(url) };
    evidence.http.push(call);
    try {
      const response = await fetchImpl(url, { ...init, signal: init.signal || AbortSignal.timeout(120000) });
      call.status = response.status;
      call.contentType = response.headers.get('content-type');
      if (!response.ok) {
        try {
          const body = await response.clone().json();
          call.errorCode = body.error?.code || body.code || null;
          call.errorMessage = scrub(body.error?.message || body.message || '').slice(0, 1200);
        } catch {
          call.errorBodyNotLogged = true;
        }
      }
      log('HTTP:', JSON.stringify(call));
      return response;
    } catch (error) {
      call.transportError = scrub(error.message).slice(0, 300);
      log('HTTP:', JSON.stringify(call));
      throw error;
    }
  };
  const report = (activity, start = false) => {
    const facts = activityFacts(activity);
    (start ? evidence.startActivities : evidence.turnActivities).push(facts);
    log(start ? 'Start activity:' : 'Turn activity:', JSON.stringify(facts));
  };
  try {
    if (args.includes('--maker-test')) {
      const id = config.environmentId.replaceAll('-', '');
      const endpoint = `https://${id.slice(0, -2)}.${id.slice(-2)}.environment.api.powerplatform.com/powervirtualagents/evaluation-test/authenticated/bots/${config.agentId}/conversations?api-version=2022-03-01-preview`;
      const post = async (url, body) => {
        const response = await diagnosticFetch(url, { method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(body) });
        if (!response.ok) throw new Error(`Evaluation HTTP ${response.status}`);
        return response.json();
      };
      evidence.startRoute = endpoint;
      const start = await post(endpoint, { emitStartConversationEvent: true, locale: 'en-US' });
      if (!start.conversationId) throw new Error('No evaluation conversation ID.');
      evidence.conversationId = start.conversationId;
      (start.activities || []).forEach(a => report(a, true));
      const turnUrl = new URL(endpoint);
      turnUrl.pathname += '/' + start.conversationId;
      evidence.turnSent = true;
      const turn = await post(turnUrl, { activity: { type: 'message', text: prompt, locale: 'en-US', conversation: { id: start.conversationId } } });
      evidence.turnState = turn.action;
      (turn.activities || []).forEach(a => report(a));
    } else {
      const settings = new ConnectionSettings({
        environmentId: config.environmentId, schemaName: config.schemaName,
        cloud: 'Prod', copilotAgentType: 'Published', enableDiagnostics: true,
        diagnosticsPseudonymKey: randomBytes(32).toString('hex')
      });
      evidence.startRoute = getCopilotStudioConnectionUrl(settings);
      log('Published SDK target:', evidence.startRoute);
      // Only this diagnostic process is instrumented. SDK request bodies/response rows are not logged.
      globalThis.fetch = diagnosticFetch;
      const client = options.clientFactory ? options.clientFactory(settings, token) : new CopilotStudioClient(settings, token);
      let conversationId;
      for await (const activity of client.startConversationStreaming({ emitStartConversationEvent: true, locale: 'en-US' })) {
        conversationId ||= activity.conversation?.id;
        report(activity, true);
      }
      if (!conversationId) throw new Error('Published SDK returned no conversation ID.');
      evidence.conversationId = conversationId;
      evidence.turnSent = true;
      for await (const activity of client.sendActivityStreaming({
        type: 'message', text: prompt, locale: 'en-US', conversation: { id: conversationId }
      }, conversationId)) report(activity);
    }
    evidence.topicFallback = evidence.turnActivities.some(a => a.text.topicFallback);
    evidence.connectionRequired = [...evidence.startActivities, ...evidence.turnActivities].some(a => a.text.connectionRequired);
    evidence.outcome = evidence.connectionRequired ? 'connection-required'
      : evidence.topicFallback ? 'topic-fallback'
        : evidence.turnActivities.length ? 'response-observed-not-yet-e2e-proof' : 'no-turn-activities';
  } catch (error) {
    evidence.outcome = 'request-failed';
    evidence.error = scrub(error.message).slice(0, 1200);
    log('Probe failed:', evidence.error);
  } finally {
    globalThis.fetch = originalFetch;
  }
  log('Outcome:', JSON.stringify({ outcome: evidence.outcome, turnSent: evidence.turnSent,
    activityTypes: evidence.turnActivities.map(a => a.type), chatEndToEndPass: false }));
  if (args.includes('--save-evidence')) {
    fs.writeFileSync(path.join(__dirname, 'runtime-probe.private.json'), JSON.stringify(evidence, null, 2));
    log('Saved body-free private evidence: runtime-probe.private.json');
  }
  return evidence;
}

module.exports = { DEFAULT_PROMPT, resolvePrompt, runProbe, activityFacts, scrub };

if (require.main === module) {
  runProbe().then(evidence => {
    process.exitCode = evidence.outcome === 'request-failed' ? 1
      : evidence.outcome === 'connection-required' ? 2
        : ['topic-fallback', 'no-turn-activities'].includes(evidence.outcome) ? 3 : 0;
  }).catch(error => { console.error('Probe setup failed:', scrub(error.message)); process.exitCode = 1; });
}
