import { ReportGenerator as OriginalReportGenerator } from '../src/ReportGenerator.js';
import { ReportGenerator as RefactoredReportGenerator } from '../src/ReportGenerator.refactored.js';

const formats = ['CSV', 'HTML', 'JSON', '', '__proto__', 'toString', null];
const roles = ['ADMIN', 'USER', 'GUEST'];
const scenarios = formats.flatMap(format => roles.map(role => [format, role]));

function createItems() {
  return [-1, 0, 499, 500, 501, 999, 1000, 1001].map((value, index) => ({
    id: index + 1,
    name: `Produto ${index + 1}`,
    value,
    priority: index === 0,
  }));
}

describe('Compatibilidade com a versão original corrigida', () => {
  it.each(scenarios)('preserva saída e mutações: formato %s, perfil %s', (format, role) => {
    const user = { name: 'Matheus', role };
    const originalItems = createItems();
    const refactoredItems = createItems();
    const original = new OriginalReportGenerator({});
    const refactored = new RefactoredReportGenerator({});

    expect(refactored.generateReport(format, user, refactoredItems))
      .toBe(original.generateReport(format, user, originalItems));
    expect(refactoredItems).toEqual(originalItems);
  });

  it('mantém os limites de visibilidade e de prioridade', () => {
    const generator = new RefactoredReportGenerator({});
    const user = { name: 'User', role: 'USER' };
    const admin = { name: 'Admin', role: 'ADMIN' };
    const items = createItems();

    const userReport = generator.generateReport('CSV', user, items);
    expect(userReport).toContain('4,Produto 4,500,User');
    expect(userReport).not.toContain('5,Produto 5,501,User');

    generator.generateReport('CSV', admin, items);
    expect(items.find(item => item.value === 1000).priority).toBe(false);
    expect(items.find(item => item.value === 1001).priority).toBe(true);
  });

  it('preserva a prioridade entre chamadas sucessivas e não destaca itens para USER', () => {
    const original = new OriginalReportGenerator({});
    const refactored = new RefactoredReportGenerator({});
    const originalItems = createItems();
    const refactoredItems = createItems();
    const users = [
      { name: 'Admin', role: 'ADMIN' },
      { name: 'User', role: 'USER' },
    ];

    for (const user of users) {
      expect(refactored.generateReport('HTML', user, refactoredItems))
        .toBe(original.generateReport('HTML', user, originalItems));
    }
    expect(refactoredItems).toEqual(originalItems);
  });
});
