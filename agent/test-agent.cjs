const { execFileSync } = require('node:child_process');
const { CopilotStudioClient } = require('@microsoft/agents-copilotstudio-client');
const config = require('./resources.json');

function cardText(value) {
  if (!value || typeof value !== 'object') return [];
  if (Array.isArray(value)) return value.flatMap(cardText);
  return [
    ...(['text', 'title'].flatMap(key => typeof value[key] === 'string' ? [value[key]] : [])),
    ...Object.entries(value).filter(([key]) => key !== 'text' && key !== 'title')
      .flatMap(([, child]) => cardText(child))
  ];
}

async function main() {
  const token = execFileSync(process.env.ComSpec || 'cmd.exe', [
    '/d', '/s', '/c',
    `az account get-access-token --resource https://api.powerplatform.com --tenant ${config.tenantId} --query accessToken -o tsv`
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  const environmentHost = config.environmentId.replaceAll('-', '');
  const testEndpoint = `https://${environmentHost.slice(0, -2)}.${environmentHost.slice(-2)}.environment.api.powerplatform.com/powervirtualagents/evaluation-test/authenticated/bots/${config.agentId}/conversations?api-version=2022-03-01-preview`;
  if (process.argv.includes('--maker-test')) {
    async function post(url, body) {
      const response = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(120000)
      });
      if (!response.ok) throw new Error(`Maker test HTTP ${response.status}`);
      return response.json();
    }
    const start = await post(testEndpoint, { emitStartConversationEvent: true, locale: 'en-US' });
    if (!start.conversationId) throw new Error('Maker test returned no conversation ID.');
    const turnUrl = new URL(testEndpoint);
    turnUrl.pathname += `/${start.conversationId}`;
    const promptIndex = process.argv.indexOf('--prompt');
    const prompt = promptIndex >= 0 ? process.argv[promptIndex + 1] : 'Run the Power BI smoke test.';
    if (!prompt) throw new Error('--prompt requires a value.');
    const turn = await post(turnUrl, { activity: {
      type: 'message', text: prompt, locale: 'en-US',
      conversation: { id: start.conversationId }
    } });
    console.log('Maker conversation:', start.conversationId);
    let needsConnection = false;
    for (const activity of turn.activities || []) {
      if (activity.text) {
        console.log('Agent:', activity.text.replace(/https?:\/\/\S+/g, '[URL omitted]'));
        needsConnection ||= /ConnectionReferenceNotFound/.test(activity.text);
      }
      for (const attachment of activity.attachments || []) {
        console.log('Attachment type:', attachment.contentType);
        for (const text of cardText(attachment.content)) {
          console.log('Card:', text.replace(/https?:\/\/\S+/g, '[URL omitted]'));
          needsConnection ||= /connection manager|verify your credentials|get you connected/i.test(text);
        }
      }
    }
    console.log('Turn state:', turn.action);
    if (needsConnection) {
      console.log('BLOCKED: runtime requests per-agent connection-manager approval. An environment connection may already exist; select it rather than creating another.');
      process.exitCode = 2;
    } else {
      console.log('Review the response: a completed chat turn alone is not a successful query test.');
    }
    return;
  }
  const client = new CopilotStudioClient({
    environmentId: config.environmentId,
    schemaName: config.schemaName,
    cloud: 'Prod',
    enableDiagnostics: false
  }, token);
  let conversationId;
  for await (const activity of client.startConversationStreaming({ emitStartConversationEvent: true, locale: 'en-US' })) {
    conversationId ||= activity.conversation?.id;
    if (activity.text) console.log('Agent:', activity.text);
  }
  if (!conversationId) throw new Error('No conversation ID returned.');
  console.log('Authenticated conversation started:', conversationId);
  for await (const activity of client.sendActivityStreaming({
    type: 'message',
    text: 'Run the Power BI smoke test.',
    conversation: { id: conversationId }
  }, conversationId)) {
    if (activity.text) console.log('Agent:', activity.text);
    for (const attachment of activity.attachments || []) {
      console.log('Attachment type:', attachment.contentType);
      if (attachment.contentType?.includes('oauth')) {
        console.log('Interactive end-user OAuth is required; no authentication tokens or sign-in URLs logged.');
      }
    }
  }
  console.log('Chat exchange completed. A response alone is not proof of successful DAX execution.');
}

main().catch(error => {
  console.error('Agent test failed:', error.message);
  process.exitCode = 1;
});
