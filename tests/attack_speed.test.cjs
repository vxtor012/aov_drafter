const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync('public/assets/js/attack-speed-data.js', 'utf8'), context);
const data = JSON.parse(JSON.stringify(context.window.ATTACK_SPEED_DATA));
const sources = new Map(data.sources.map(source => [source.id, source]));
assert.equal(sources.size, data.sources.length);
assert.equal(data.verified_game_patch, null);
assert.equal(data.heroes.length, 130);
assert.equal(new Set(data.heroes.map(hero => hero.id)).size, 130);
for (const model of Object.values(data.models)) {
    assert.equal(model.rows[0].percent, 0);
    model.rows.forEach((row, index) => {
        assert(Number.isFinite(row.percent) && row.percent >= 0);
        assert(row.frames >= 6);
        assert(row.sources.length && row.sources.every(id => sources.has(id)));
        if (index) {
            assert(row.percent > model.rows[index - 1].percent);
            assert.equal(row.frames, model.rows[index - 1].frames - 1);
        }
    });
}
const at = (model, frame) => data.models[model].rows.find(row => row.frames === frame);
assert.equal(at('C', 10).percent, 68.2);
assert.equal(at('F', 10).percent, 183.6);
assert.equal(at('H', 6).percent, 141.8);
assert.equal(at('H-1f', 6).percent, 101.6);
assert.deepEqual(at('F', 25).sources, ['bahamut2024']);
const hero = id => data.heroes.find(entry => entry.id === id);
for (const entry of data.heroes) {
    assert(entry.evidence.every(id => sources.has(id)));
    assert(entry.forms.length > 0);
    for (const form of entry.forms) assert(form.model === null || data.models[form.model]);
}
assert.equal(hero('preyta').forms[0].model, 'E');
assert.equal(hero('preyta').forms[0].status, 'partial');
assert(hero('preyta').evidence.includes('preyta2025'));
assert.match(hero('preyta').note, /178/);
assert.equal(hero('boltbaron').forms[0].model, 'H');
assert.equal(hero('stuart').forms[0].model, 'C');
assert.equal(hero('sinestrea').forms[0].model, 'H');
for (const id of ['heino', 'fennik', 'butterfly', 'marja', 'capheny']) assert.equal(hero(id).forms[0].model, null);
assert(data.heroes.some(entry => entry.forms.some(form => form.status === 'unknown')));
assert(!fs.existsSync('public/assets/js/attack-speed-engine.js'));
assert(!/dialog|type="number"|attack-speed-engine/.test(fs.readFileSync('public/attack-speed.html', 'utf8')));
console.log('PASS: source references, ordered frame thresholds, measured anchors, exceptions and no calculator');
