const chalk = require('chalk');

const BRAND = chalk.bold.hex('#4F8EF7');
const DIM = chalk.gray;
const SUCCESS = chalk.green;
const WARN = chalk.yellow;
const ERR = chalk.red;
const ACCENT = chalk.cyan;
const HIGHLIGHT = chalk.white.bold;

function banner() {
    console.log('');
    console.log(BRAND('  ╔══════════════════════════════════════╗'));
    console.log(BRAND('  ║') + HIGHLIGHT('   NAMANGO ') + DIM('AI Gateway Platform') + BRAND('      ║'));
    console.log(BRAND('  ╚══════════════════════════════════════╝'));
    console.log('');
}

function sectionHeader(title) {
    console.log('');
    console.log(BRAND('  --- ') + HIGHLIGHT(title) + BRAND(' ---'));
    console.log('');
}

function keyValue(key, value, indent = 4) {
    const pad = ' '.repeat(indent);
    console.log(`${pad}${DIM(key + ':')} ${chalk.white(value)}`);
}

function table(headers, rows) {
    const Table = require('cli-table3');
    const t = new Table({
        head: headers.map(h => ACCENT(h)),
        chars: {
            'top': '─', 'top-mid': '┬', 'top-left': '┌', 'top-right': '┐',
            'bottom': '─', 'bottom-mid': '┴', 'bottom-left': '└', 'bottom-right': '┘',
            'left': '│', 'left-mid': '├', 'mid': '─', 'mid-mid': '┼',
            'right': '│', 'right-mid': '┤', 'middle': '│',
        },
        style: { head: [], border: ['gray'] },
    });
    rows.forEach(r => t.push(r));
    console.log(t.toString());
}

function spinner(text) {
    const ora = require('ora');
    return ora({ text, color: 'cyan', spinner: 'dots' }).start();
}

module.exports = { BRAND, DIM, SUCCESS, WARN, ERR, ACCENT, HIGHLIGHT, banner, sectionHeader, keyValue, table, spinner };
