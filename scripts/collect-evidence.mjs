import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ESLint } from 'eslint';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destination = join(root, 'docs', 'evidencias');
mkdirSync(destination, { recursive: true });

function execute(args, expectedStatus, filename) {
  const result = spawnSync(process.execPath, args, { cwd: root, encoding: 'utf8' });
  assert.ifError(result.error);
  const output = `${result.stdout}${result.stderr}`.replaceAll(`${root}/`, '');
  writeFileSync(join(destination, filename), `$ node ${args.join(' ')}\n\n${output}`.trimEnd() + '\n');
  assert.equal(result.status, expectedStatus, output);
}

const eslint = new ESLint({ cwd: root });
const before = await eslint.lintFiles(['src/ReportGenerator.js']);
const after = await eslint.lintFiles(['src/ReportGenerator.refactored.js']);
writeFileSync(join(destination, 'eslint-antes.json'), JSON.stringify(before, null, 2) + '\n');
writeFileSync(join(destination, 'eslint-depois.json'), JSON.stringify(after, null, 2) + '\n');
execute(['node_modules/eslint/bin/eslint.js', 'src/'], 1, 'eslint-antes.txt');
execute(['node_modules/eslint/bin/eslint.js', 'src/ReportGenerator.refactored.js'], 0, 'eslint-depois.txt');
execute([
  '--experimental-vm-modules', 'node_modules/jest/bin/jest.js', '--runInBand',
  '--runTestsByPath', 'tests/ReportGenerator.test.js',
], 0, 'testes-original.txt');
execute([
  '--experimental-vm-modules', 'node_modules/jest/bin/jest.js', '--runInBand',
  '--json', '--outputFile=docs/evidencias/testes.json',
], 0, 'testes.txt');

const originalTest = readFileSync(join(root, 'tests/ReportGenerator.test.js'), 'utf8');
const copy = readFileSync(join(root, '__tests__/ReportGenerator.refactored.test.js'), 'utf8');
assert.equal(copy, originalTest.replace(
  "from '../src/ReportGenerator.js'", "from '../src/ReportGenerator.refactored.js'",
));

const complexityLinter = new ESLint({
  cwd: root,
  overrideConfig: { rules: { 'sonarjs/cognitive-complexity': ['error', 0] } },
});
const complexityResults = await complexityLinter.lintFiles([
  'src/ReportGenerator.js', 'src/ReportGenerator.refactored.js',
]);
const complexities = complexityResults.map(result => result.messages
  .filter(message => message.ruleId === 'sonarjs/cognitive-complexity')
  .map(message => ({
    line: message.line,
    complexity: Number(message.message.match(/from (\d+) to/)[1]),
  })));
const tests = JSON.parse(readFileSync(join(destination, 'testes.json'), 'utf8'));
const methodLine = readFileSync(join(root, 'src/ReportGenerator.refactored.js'), 'utf8')
  .split('\n').findIndex(line => line.includes('generateReport(reportType')) + 1;
const summary = {
  cognitiveComplexityLimit: 5,
  originalComplexity: complexities[0][0].complexity,
  refactoredMethodComplexity: complexities[1].find(entry => entry.line === methodLine).complexity,
  refactoredMaximumComplexity: Math.max(...complexities[1].map(entry => entry.complexity)),
  originalLintErrors: before.reduce((count, result) => count + result.errorCount, 0),
  refactoredLintErrors: after.reduce((count, result) => count + result.errorCount, 0),
  passedTests: tests.numPassedTests,
  totalTests: tests.numTotalTests,
  passedSuites: tests.numPassedTestSuites,
  originalTestCopyMatches: true,
};
writeFileSync(join(destination, 'resumo.json'), JSON.stringify(summary, null, 2) + '\n');
assert.equal(summary.refactoredLintErrors, 0);
assert.equal(tests.success, true);
console.log(JSON.stringify(summary, null, 2));
