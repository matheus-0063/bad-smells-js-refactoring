# Detecção de Bad Smells e Refatoração Segura

Trabalho de Testes de Software de **Matheus Fernandes de Oliveira**, matrícula **773220**.

O projeto gera relatórios CSV e HTML para os perfis ADMIN e USER. A versão refatorada separa as regras de acesso e de prioridade da formatação, mantendo os resultados e os efeitos sobre os itens da versão original corrigida.

## Executar

Com Node.js 18 ou superior e npm:

```bash
npm ci
npm test
npm run lint
```

Os resultados registrados são **33 testes aprovados em 3 suítes** e **zero erros de lint no arquivo refatorado**. As versões das dependências estão fixadas pelo `package-lock.json`.

## Arquivos da entrega

- [`src/ReportGenerator.refactored.js`](src/ReportGenerator.refactored.js): implementação refatorada.
- [`__tests__/ReportGenerator.refactored.test.js`](__tests__/ReportGenerator.refactored.test.js): cópia dos testes fornecidos, com alteração apenas do import.
- [`tests/ReportGenerator.test.js`](tests/ReportGenerator.test.js): testes originais, sem alterações. O repositório recebido usa `tests/`, embora o enunciado mencione `__tests__/`.
- [`__tests__/ReportGenerator.compatibility.test.js`](__tests__/ReportGenerator.compatibility.test.js): 23 verificações adicionais de compatibilidade, valores de fronteira e prioridade.
- [`output/pdf/relatorio-bad-smells.pdf`](output/pdf/relatorio-bad-smells.pdf): relatório de 4 páginas para entrega.
- [`docs/RELATORIO.md`](docs/RELATORIO.md): conteúdo editável do relatório.
- [`docs/evidencias/`](docs/evidencias/): saídas reais do ESLint e dos testes, imagem da saída do linter e resumo das métricas.

## Problemas anteriores à refatoração

O projeto recebido não iniciou com todos os testes passando:

1. `npm test` falhava com `Cannot use import statement outside a module`. O script passou a executar o Jest com `node --experimental-vm-modules`, conforme a [documentação do Jest 29.7](https://jestjs.io/docs/29.7/ecmascript-modules).
2. Com os módulos habilitados, passavam 4 de 5 testes. O HTML para ADMIN produzia `<tr >` em itens sem prioridade, enquanto o teste exigia `<tr>`. Foram corrigidas somente as duas linhas responsáveis pelo espaço em `src/ReportGenerator.js`, antes de iniciar a refatoração. Nenhum teste original foi alterado.

Essa correção mínima é uma exceção documentada à preservação do arquivo original solicitada no enunciado: ela permite estabelecer a rede de segurança de 5/5 testes. As demais mudanças de design estão exclusivamente no arquivo `.refactored.js`.

## Smells e técnicas aplicadas

| Problema | Mudança |
| --- | --- |
| Método longo com complexidade cognitiva 27 | Extração de funções de acesso, prioridade e composição do corpo; `generateReport` passa a ter complexidade 2. |
| Condicionais aninhadas por perfil e formato | Condição de guarda, predicado `canViewItem` e estratégias de formatação com uma interface comum. |
| Duplicação de linhas CSV e soma dos totais | Um único fluxo de itens visíveis renderiza a linha e acumula o total. |
| Números mágicos 500 e 1000 | Constantes `STANDARD_USER_VALUE_LIMIT` e `ADMIN_PRIORITY_THRESHOLD`. |

O limite de complexidade do ESLint foi mantido em **5**, mais rigoroso que o valor 15 sugerido no enunciado. A maior complexidade de uma função refatorada é **4**. Não foram desativadas regras para obter a aprovação.

## Análises e evidências

```bash
npm run lint             # Aprova a versão refatorada
npm run lint:original    # Reporta os 2 erros de smell do original
npm run lint:all         # Examina src/; continua reportando os erros do original
npm run evidence        # Reexecuta linter e testes e grava docs/evidencias/
```

Os comandos `lint:original` e `lint:all` retornam código 1 intencionalmente, pois o original foi mantido com seus smells para comparação. O comando padrão `lint` verifica a implementação que será avaliada como refatorada.

As verificações adicionais comparam as saídas completas e as mutações dos itens entre as duas versões, em 21 combinações de formato e perfil. Também cobrem os limites 500/501 e 1000/1001 e chamadas consecutivas. Foram preservados o retorno vazio para formatos desconhecidos e a marcação de prioridade de ADMIN mesmo nesses formatos.

## Regerar o relatório

O PDF já está pronto; Python é necessário apenas para regenerá-lo:

```bash
python3 -m pip install -r requirements-relatorio.txt
npm run evidence
python3 scripts/generate_report.py
```

A capa usa os dados de [`docs/dados-relatorio.json`](docs/dados-relatorio.json). A imagem do linter é renderizada a partir da saída real gravada em `eslint-antes.txt`; ela não representa uma captura da interface de um aplicativo de terminal.

Projeto-base: [CleitonSilvaT/bad-smells-js-refactoring](https://github.com/CleitonSilvaT/bad-smells-js-refactoring). Fork de entrega: [matheus-0063/bad-smells-js-refactoring](https://github.com/matheus-0063/bad-smells-js-refactoring).
