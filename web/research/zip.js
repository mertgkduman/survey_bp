/* Minimal deterministic ZIP writer for portable research packages; no CDN or compression. */
(function (global) {
  "use strict";
  var enc = new TextEncoder();
  var crcTable = new Uint32Array(256);
  for (var n = 0; n < 256; n += 1) { var c = n; for (var k = 0; k < 8; k += 1) c = (c >>> 1) ^ ((c & 1) ? 0xedb88320 : 0); crcTable[n] = c >>> 0; }
  function crc32(bytes) { var crc = 0xffffffff; for (var i = 0; i < bytes.length; i += 1) crc = (crc >>> 8) ^ crcTable[(crc ^ bytes[i]) & 255]; return (crc ^ 0xffffffff) >>> 0; }
  function u16(value) { return new Uint8Array([value & 255, (value >>> 8) & 255]); }
  function u32(value) { return new Uint8Array([value & 255, (value >>> 8) & 255, (value >>> 16) & 255, (value >>> 24) & 255]); }
  function join(parts) { var size = parts.reduce(function (sum, part) { return sum + part.length; }, 0), out = new Uint8Array(size), offset = 0; parts.forEach(function (part) { out.set(part, offset); offset += part.length; }); return out; }
  function dateParts(date) { var d = date || new Date("1980-01-01T00:00:00Z"); return { time: (d.getUTCHours() << 11) | (d.getUTCMinutes() << 5) | Math.floor(d.getUTCSeconds() / 2), date: ((d.getUTCFullYear() - 1980) << 9) | ((d.getUTCMonth() + 1) << 5) | d.getUTCDate() }; }
  function header(signature, layout, values) { var chunks = [u32(signature)]; layout.forEach(function (width, index) { chunks.push(width === 2 ? u16(values[index]) : u32(values[index])); }); return join(chunks); }
  function create(files) {
    var offset = 0, bodies = [], central = [], stamp = dateParts();
    files.slice().sort(function (a, b) { return a.name.localeCompare(b.name); }).forEach(function (file) {
      var name = enc.encode(file.name.replace(/\\/g, "/")), bytes = typeof file.content === "string" ? enc.encode(file.content) : file.content, crc = crc32(bytes);
      var local = join([header(0x04034b50, [2,2,2,2,2,4,4,4,2,2], [20, 0, 0, stamp.time, stamp.date, crc, bytes.length, bytes.length, name.length, 0]), name, bytes]);
      bodies.push(local);
      central.push(join([header(0x02014b50, [2,2,2,2,2,2,4,4,4,2,2,2,2,2,4,4], [20, 20, 0, 0, stamp.time, stamp.date, crc, bytes.length, bytes.length, name.length, 0, 0, 0, 0, 0, offset]), name]));
      offset += local.length;
    });
    var centralBytes = join(central), end = join([u32(0x06054b50), u16(0), u16(0), u16(files.length), u16(files.length), u32(centralBytes.length), u32(offset), u16(0)]);
    return new Blob([join(bodies), centralBytes, end], { type: "application/zip" });
  }
  global.ResearchZip = { create: create, crc32: crc32 };
})(window);
