import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { getSafeHttpUrl } from './safeUrl.js';

describe('safeUrl', () => {
  it('allows safe http and https URLs', () => {
    assert.equal(getSafeHttpUrl('https://example.com/path'), 'https://example.com/path');
    assert.equal(getSafeHttpUrl('http://example.com/path'), 'http://example.com/path');
  });

  it('rejects unsupported or malformed URLs', () => {
    assert.equal(getSafeHttpUrl('javascript:alert(1)'), null);
    assert.equal(getSafeHttpUrl('data:text/html,<p>bad</p>'), null);
    assert.equal(getSafeHttpUrl('/relative/path'), null);
    assert.equal(getSafeHttpUrl('not a url'), null);
    assert.equal(getSafeHttpUrl(undefined), null);
  });
});
