import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  MAX_SESSION_QUESTIONS,
  SESSION_LIMIT_KEY,
  canAskQuestion,
  getQuestionCount,
  getRemainingQuestions,
  incrementQuestionCount,
  resetQuestionCount,
} from './sessionLimit.js';
import { MemoryStorage } from './testStorage.js';

describe('sessionLimit', () => {
  it('allows ten questions and blocks the eleventh', () => {
    const storage = new MemoryStorage();

    for (let count = 1; count <= MAX_SESSION_QUESTIONS; count += 1) {
      assert.equal(canAskQuestion(storage), true);
      assert.equal(incrementQuestionCount(storage), count);
    }

    assert.equal(canAskQuestion(storage), false);
    assert.equal(incrementQuestionCount(storage), MAX_SESSION_QUESTIONS);
    assert.equal(getRemainingQuestions(storage), 0);
  });

  it('resets the browser session question count', () => {
    const storage = new MemoryStorage();
    incrementQuestionCount(storage);
    resetQuestionCount(storage);

    assert.equal(getQuestionCount(storage), 0);
    assert.equal(canAskQuestion(storage), true);
  });

  it('clamps corrupted counts above the per-session maximum', () => {
    const storage = new MemoryStorage();
    storage.setItem(SESSION_LIMIT_KEY, String(MAX_SESSION_QUESTIONS + 999));

    assert.equal(getQuestionCount(storage), MAX_SESSION_QUESTIONS);
    assert.equal(canAskQuestion(storage), false);
    assert.equal(getRemainingQuestions(storage), 0);
  });
});
