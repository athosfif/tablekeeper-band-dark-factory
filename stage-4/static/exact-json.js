'use strict';

// The API has no safe-integer ceiling. Never pass its numeric tokens through
// binary floating point: integers use BigInt, other decimals retain their token.
const ExactJSON = (() => {
  const numberToken = /-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
  class Decimal {
    constructor(token) { this.token = token; Object.freeze(this); }
    toString() { return this.token; }
  }
  function parse(text) {
    let at = 0;
    const fail = () => { throw new SyntaxError(`Invalid JSON at character ${at}`); };
    const whitespace = () => { while (/[\t\n\r ]/.test(text[at] || '\0')) at++; };
    function string() {
      const start = at++;
      while (at < text.length) {
        const char = text[at++];
        if (char === '"') return JSON.parse(text.slice(start, at));
        if (char === '\\') at++;
      }
      return fail();
    }
    function value() {
      whitespace();
      const char = text[at];
      if (char === '"') return string();
      if (char === '[' || char === '{') {
        const object = char === '{', result = object ? {} : [], end = object ? '}' : ']';
        at++; whitespace();
        if (text[at] === end) { at++; return result; }
        while (true) {
          if (object) {
            whitespace(); if (text[at] !== '"') return fail();
            const key = string(); whitespace(); if (text[at++] !== ':') return fail();
            // __proto__ is ordinary JSON data, never a prototype assignment.
            Object.defineProperty(result, key, {value:value(), enumerable:true, writable:true, configurable:true});
          } else result.push(value());
          whitespace();
          if (text[at] === end) { at++; return result; }
          if (text[at++] !== ',') return fail();
        }
      }
      for (const [literal, result] of [['true',true], ['false',false], ['null',null]]) {
        if (text.startsWith(literal, at)) { at += literal.length; return result; }
      }
      numberToken.lastIndex = at;
      const match = numberToken.exec(text);
      if (!match) return fail();
      at = numberToken.lastIndex;
      return /[.eE]/.test(match[0]) ? new Decimal(match[0]) : BigInt(match[0]);
    }
    const result = value(); whitespace();
    if (at !== text.length) return fail();
    return result;
  }
  function stringify(value) {
    if (typeof value === 'bigint') return value.toString();
    if (value instanceof Decimal) return value.token;
    if (Array.isArray(value)) return '[' + value.map(item => stringify(item) ?? 'null').join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).flatMap(key => {
      const encoded = stringify(value[key]);
      return encoded === undefined ? [] : [JSON.stringify(key) + ':' + encoded];
    }).join(',') + '}';
    return JSON.stringify(value);
  }
  // Validate the decimal spelling itself, including fractional/exponent input.
  // Native number-input step validation and valueAsNumber can silently round.
  function positiveInteger(value) {
    const match = /^(\+?)(\d+(?:\.\d*)?|\.\d+)(?:[eE]([+-]?\d+))?$/.exec(String(value));
    if (!match) throw new RangeError('Enter a whole number of guests, at least 1.');
    const [whole, fraction = ''] = match[2].split('.');
    let digits = (whole + fraction).replace(/^0+/, '');
    if (!digits) throw new RangeError('Enter a whole number of guests, at least 1.');
    const scale = BigInt(match[3] || '0') - BigInt(fraction.length);
    if (scale < 0n) {
      const places = -scale;
      if (places >= BigInt(digits.length)) throw new RangeError('Enter a whole number of guests, at least 1.');
      // This conversion is bounded by the actual input string's length, not its value.
      const split = digits.length - Number(places);
      if (!/^0+$/.test(digits.slice(split))) throw new RangeError('Enter a whole number of guests, at least 1.');
      digits = digits.slice(0, split);
    }
    return BigInt(digits) * (scale > 0n ? 10n ** scale : 1n);
  }
  return Object.freeze({parse, stringify, positiveInteger});
})();
