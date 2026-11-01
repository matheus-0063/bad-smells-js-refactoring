const STANDARD_USER_VALUE_LIMIT = 500;
const ADMIN_PRIORITY_THRESHOLD = 1000;

const csvFormatter = {
  header() {
    return 'ID,NOME,VALOR,USUARIO\n';
  },

  row(item, user) {
    return `${item.id},${item.name},${item.value},${user.name}\n`;
  },

  footer(total) {
    return `\nTotal,,\n${total},,\n`;
  },
};

const htmlFormatter = {
  header(user) {
    return '<html><body>\n'
      + '<h1>Relatório</h1>\n'
      + `<h2>Usuário: ${user.name}</h2>\n`
      + '<table>\n'
      + '<tr><th>ID</th><th>Nome</th><th>Valor</th></tr>\n';
  },

  row(item, user) {
    const isPriority = user.role === 'ADMIN' && item.priority;
    const style = isPriority ? ' style="font-weight:bold;"' : '';
    return `<tr${style}><td>${item.id}</td><td>${item.name}</td><td>${item.value}</td></tr>\n`;
  },

  footer(total) {
    return `</table>\n<h3>Total: ${total}</h3>\n</body></html>\n`;
  },
};

const FORMATTERS = new Map([
  ['CSV', csvFormatter],
  ['HTML', htmlFormatter],
]);

function canViewItem(user, item) {
  return user.role === 'ADMIN'
    || (user.role === 'USER' && item.value <= STANDARD_USER_VALUE_LIMIT);
}

function updatePriority(user, item) {
  if (user.role === 'ADMIN' && item.value > ADMIN_PRIORITY_THRESHOLD) {
    item.priority = true;
  }
}

function createReportBody(formatter, user, items) {
  let body = '';
  let total = 0;

  for (const item of items) {
    // O original também altera a prioridade para formatos desconhecidos.
    updatePriority(user, item);
    if (!formatter || !canViewItem(user, item)) {
      continue;
    }

    body += formatter.row(item, user);
    total += item.value;
  }

  return { body, total };
}

export class ReportGenerator {
  constructor(database) {
    this.db = database;
  }

  generateReport(reportType, user, items) {
    const formatter = FORMATTERS.get(reportType);
    const header = formatter?.header(user) ?? '';
    const { body, total } = createReportBody(formatter, user, items);
    return `${header}${body}${formatter?.footer(total) ?? ''}`.trim();
  }
}
