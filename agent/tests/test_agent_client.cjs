const test = require('node:test');
const assert = require('node:assert/strict');
const { DEFAULT_PROMPT, resolvePrompt, runProbe, activityFacts } = require('../test-agent.cjs');

const fakeId = digit => [8, 4, 4, 4, 12].map(length => digit.repeat(length)).join('-');
const config = {
  environmentId: fakeId('1'),
  agentId: fakeId('2'),
  tenantId: fakeId('3'),
  schemaName: 'example_agent'
};

test('default is metadata, and malformed prompts fail before network calls', () => {
  assert.equal(resolvePrompt([]), DEFAULT_PROMPT);
  assert.match(DEFAULT_PROMPT, /tables and measures/);
  assert.throws(() => resolvePrompt(['--prompt']));
});

test('published SDK forwards the exact custom prompt into a fresh conversation', async () => {
  const prompt = 'Which relationships exist in the primary model?';
  let sent, settings, start;
  const evidence = await runProbe({
    args: ['--prompt', prompt], config, token: 'synthetic-test-token', log() {},
    clientFactory(value) {
      settings = value;
      return {
        async * startConversationStreaming(request) {
          start = request;
          yield { type: 'event', conversation: { id: 'fresh-test-conversation' } };
        },
        async * sendActivityStreaming(activity) {
          sent = activity;
          yield { type: 'message', text: 'Schema response', conversation: activity.conversation };
        }
      };
    }
  });
  assert.equal(sent.text, prompt);
  assert.equal(sent.conversation.id, 'fresh-test-conversation');
  assert.equal(start.emitStartConversationEvent, true);
  assert.equal(settings.copilotAgentType, 'Published');
  assert.equal(settings.enableDiagnostics, true);
  assert.match(evidence.startRoute, /copilotstudio\/dataverse-backed\/authenticated\/bots\/example_agent/);
  assert.equal(evidence.turnSent, true);
  assert.equal(evidence.chatEndToEndPass, false);
});

test('evaluation route forwards the same prompt and classifies actual fallback', async () => {
  const bodies = [];
  const evidence = await runProbe({
    args: ['--maker-test', '--prompt', 'Exact metadata intent'], config,
    token: 'synthetic-test-token', log() {},
    fetchImpl: async (_url, init) => {
      bodies.push(JSON.parse(init.body));
      return new Response(JSON.stringify(bodies.length === 1
        ? { conversationId: 'test-evaluation', activities: [] }
        : { action: 'waiting', activities: [{ type: 'message', text: 'Sorry, I am not able to find a related topic. Can you rephrase and try again?' }] }),
      { status: 200, headers: { 'content-type': 'application/json' } });
    }
  });
  assert.equal(bodies[1].activity.text, 'Exact metadata intent');
  assert.equal(evidence.outcome, 'topic-fallback');
});

test('diagnostics do not copy business rows, identities, DAX literals or credentials', () => {
  const facts = activityFacts({
    type: 'trace', name: 'plan',
    text: 'Private Person private@example.invalid 981234',
    value: {
      dialogId: 'example_agent.topic.GeneratedDaxQuery',
      tableExpression: 'ROW("Private Person", 981234)',
      rows: [{ Owner: 'private@example.invalid', Value: 981234 }]
    }
  });
  const encoded = JSON.stringify(facts);
  assert.ok(!encoded.includes('Private Person'));
  assert.ok(!encoded.includes('private@example.invalid'));
  assert.ok(!encoded.includes('981234'));
  assert.ok(facts.structuredHints.some(h => h.component === 'GeneratedDaxQuery'));
  assert.ok(facts.structuredHints.some(h => h.sha256));
});

test('SDK creation failure is not reported as a sent prompt or a chat pass', async () => {
  const evidence = await runProbe({
    args: ['--prompt', 'Metadata first'], config, token: 'synthetic-test-token', log() {},
    clientFactory: () => ({
      async * startConversationStreaming() { throw new Error('HTTP 403 insufficient_scope'); },
      async * sendActivityStreaming() { assert.fail('Must not send a turn without a conversation'); }
    })
  });
  assert.equal(evidence.outcome, 'request-failed');
  assert.equal(evidence.turnSent, false);
  assert.equal(evidence.chatEndToEndPass, false);
});
