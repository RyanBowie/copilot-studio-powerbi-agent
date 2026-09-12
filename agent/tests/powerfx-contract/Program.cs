using System.Text.Json;
using Microsoft.PowerFx;

if (args.Length != 2)
    throw new ArgumentException("Provide synthetic-case JSON and result JSON paths.");
var config = new PowerFxConfig(Features.PowerFxV1);
config.EnableJsonFunctions();
var engine = new RecalcEngine(config);
var options = new ParserOptions { AllowsSideEffects = true };
var cases = JsonDocument.Parse(File.ReadAllText(args[0])).RootElement;
var evidence = new List<object>();
var failures = 0;
foreach (var item in cases.EnumerateArray())
{
    var name = item.GetProperty("name").GetString();
    var expected = item.GetProperty("expected");
    var passed = false;
    try
    {
        var value = await engine.EvalAsync(item.GetProperty("expression").GetString()!,
                                          CancellationToken.None, options: options);
        var actual = JsonSerializer.SerializeToElement(value.ToObject());
        if (item.TryGetProperty("parseResultJson", out var parseJson) && parseJson.GetBoolean())
            actual = JsonDocument.Parse(actual.GetString()!).RootElement.Clone();
        passed = JsonElement.DeepEquals(actual, expected);
        evidence.Add(new { name, passed, actual, expected });
    }
    catch (Exception error)
    {
        var exceptionType = error.GetType().FullName;
        passed = item.TryGetProperty("allowedClosedException", out var allowed) &&
                 allowed.GetString() == exceptionType;
        evidence.Add(new { name, passed, exceptionType,
                          missingAssembly = error is FileNotFoundException missing ? Path.GetFileName(missing.FileName) : null,
                          schemaVisibilityEstablished = false });
    }
    if (!passed)
        failures++;
    Console.WriteLine($"{(passed ? "PASS" : "FAIL")} {name}");
}
File.WriteAllText(args[1], JsonSerializer.Serialize(new {
    engine = "Microsoft.PowerFx.RecalcEngine; synthetic typed connector-response fixtures, not cloud chat",
    runtimeAssembly = typeof(RecalcEngine).Assembly.FullName,
    cases = evidence,
    passed = evidence.Count - failures,
    failed = failures
}, new JsonSerializerOptions { WriteIndented = true }));
if (failures != 0)
    Environment.ExitCode = 1;
