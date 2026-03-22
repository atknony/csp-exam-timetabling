/**
 * excelExport.js — Official university template Excel export (styled).
 *
 * Generates a 3-sheet workbook that is visually indistinguishable from
 * the official Okan University exam schedule templates.
 *
 * Library: xlsx-js-style (free MIT fork of SheetJS with cell styling)
 *   npm install xlsx-js-style
 *
 * Style forensics extracted from the official template:
 *   Sheet 1 headers:  Calibri 14 bold, bg #FFFF99 / #EDF765, merged A:G
 *   Column headers:   Calibri 12 bold, thin borders all sides
 *   Date separators:  Calibri 12 bold, bg #FFC000 (amber), merged A:G
 *   Data cells:       Calibri 11, thin borders, left/center alignment
 *   Sheet 2 headers:  Calibri 11 bold, bg #FFFF00, thin borders
 *   Sheet 3:          Times 10–16, thin borders, merged header A1:D1
 */

import XLSX from "xlsx-js-style";


/* ────────────────────────────────────────────────────────────
   CONSTANTS
   ──────────────────────────────────────────────────────────── */

const WEEKDAY_TR = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const PERIOD_TIMES = [
  "08:50-10:20", "10:30-12:00", "13:00-14:30",
  "14:40-16:10", "16:20-17:50", "18:00-19:30", "19:40-21:10",
];

/* ── Reusable style fragments ────────────────────────────── */

const B_THIN = { style: "thin", color: { rgb: "000000" } };
const BORDER_ALL = { top: B_THIN, bottom: B_THIN, left: B_THIN, right: B_THIN };
const BORDER_L   = { left: B_THIN };
const BORDER_LTB = { top: B_THIN, bottom: B_THIN, left: B_THIN };

const FONT_CAL = (sz, bold = false) => ({ name: "Calibri", sz, bold });
const FONT_TIMES = (sz, bold = false) => ({ name: "Times New Roman", sz, bold });

const FILL = (rgb) => ({ fgColor: { rgb }, patternType: "solid" });

const ALIGN_CC = { horizontal: "center", vertical: "center" };
const ALIGN_CC_WRAP = { horizontal: "center", vertical: "center", wrapText: true };
const ALIGN_LC = { horizontal: "left", vertical: "center" };
const ALIGN_LC_WRAP = { horizontal: "left", vertical: "center", wrapText: true };


/* ────────────────────────────────────────────────────────────
   HELPERS
   ──────────────────────────────────────────────────────────── */

function buildLookups(pd) {
  const tsMap = {}, roomMap = {}, instrMap = {}, examMap = {};
  for (const ts of pd.timeslots) tsMap[ts.id] = ts;
  for (const r of pd.rooms) roomMap[r.id] = r;
  for (const i of pd.instructors) instrMap[i.id] = i;
  for (const e of pd.exams) examMap[e.id] = e;
  return { tsMap, roomMap, instrMap, examMap };
}

function nextMonday() {
  const d = new Date();
  const day = d.getDay();
  const diff = day === 0 ? 1 : day === 1 ? 0 : 8 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(base, n) {
  const d = new Date(base);
  d.setDate(d.getDate() + n);
  return d;
}

function fmtDateTR(date) {
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  return `${dd}.${mm}.${date.getFullYear()} ${WEEKDAY_TR[date.getDay()]}`;
}

function resolveTime(periodIdx, meta) {
  if (meta?.periodTimes?.[periodIdx]) return meta.periodTimes[periodIdx];
  return periodIdx < PERIOD_TIMES.length ? PERIOD_TIMES[periodIdx] : `Period ${periodIdx + 1}`;
}

/** Encode a column-row pair as an Excel cell ref (0-indexed) */
function cr(c, r) { return XLSX.utils.encode_cell({ c, r }); }

/** Set a cell with value + style */
function setCell(ws, c, r, v, s) {
  const ref = cr(c, r);
  ws[ref] = { v, t: typeof v === "number" ? "n" : "s", s };
}


/* ────────────────────────────────────────────────────────────
   SHEET 1 — EXAM SCHEDULE
   Row 1: TR header (merged A1:G1, bg #FFFF99, Calibri 14 bold, h=77.25)
   Row 2: EN header (merged A2:G2, bg #EDF765, Calibri 14 bold, h=77.25)
   Row 3: Column headers (Calibri 12 bold, thin borders)
   Date separator rows: merged A:G, bg #FFC000, Calibri 12 bold, h=15.75
   Data rows: Calibri 11, thin borders, h≈30
   ──────────────────────────────────────────────────────────── */

function buildScheduleSheet(pd, sr, meta, lookups) {
  const { tsMap, roomMap, instrMap, examMap } = lookups;
  const { exam_time, exam_room, assigned_invigilators } = sr.solution;
  const hasRealDates = !!meta?.startDate;
  const base = hasRealDates ? new Date(meta.startDate) : null;

  const uniTR  = meta?.universityNameTR || "[Üniversite Adı]";
  const facTR  = meta?.facultyNameTR    || "[Fakülte Adı]";
  const termTR = meta?.termTR           || "[Dönem]";
  const typeTR = meta?.scheduleTypeTR   || "Sınav Programı";
  const uniEN  = meta?.universityName   || "[University Name]";
  const facEN  = meta?.facultyName      || "[Faculty Name]";
  const termEN = meta?.term             || "[Term]";
  const typeEN = meta?.scheduleType     || "Exam Schedule";

  const ws = {};
  const merges = [];
  const rowHts = {};
  let R = 0;

  /* ── Row 1: Turkish header ── */
  setCell(ws, 0, R, `${uniTR}\n${facTR}\n${termTR}\n${typeTR}`, {
    font: FONT_CAL(14, true), fill: FILL("FFFF99"),
    alignment: ALIGN_CC_WRAP, border: { ...BORDER_ALL },
  });
  for (let c = 1; c <= 6; c++) setCell(ws, c, R, "", {
    fill: FILL("FFFF99"), border: { ...BORDER_ALL },
  });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 6 } });
  rowHts[R] = 77.25;
  R++;

  /* ── Row 2: English header ── */
  setCell(ws, 0, R, `${uniEN}\n${facEN}\n${termEN}\n${typeEN}`, {
    font: FONT_CAL(14, true), fill: FILL("EDF765"),
    alignment: ALIGN_CC_WRAP, border: { ...BORDER_ALL },
  });
  for (let c = 1; c <= 6; c++) setCell(ws, c, R, "", {
    fill: FILL("EDF765"), border: { ...BORDER_ALL },
  });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 6 } });
  rowHts[R] = 77.25;
  R++;

  /* ── Row 3: Column headers (bilingual) ── */
  const hdrs = [
    ["Ders Kodu\nCourse Code",   "center"],
    ["Ders Adı\nCourse Name",    "left"],
    ["Öğretim Elemanı\nInstructor", "left"],
    ["Gün\nDate",                "center"],
    ["Saat\nTime",               "center"],
    ["Öğrenci Sayısı\nStudents", "center"],
    ["Derslik\nClassroom",       "center"],
  ];
  hdrs.forEach(([txt, hAlign], c) => {
    setCell(ws, c, R, txt, {
      font: FONT_CAL(12, true),
      alignment: { horizontal: hAlign, vertical: "center", wrapText: true },
      border: { ...BORDER_ALL },
    });
  });
  rowHts[R] = 33;
  R++;

  /* ── Group placed exams by day ── */
  const placed = Object.keys(exam_time).map(Number);
  const dayGroups = {};
  for (const eid of placed) {
    const ts = tsMap[exam_time[eid]];
    if (!ts) continue;
    (dayGroups[ts.day] ??= []).push({ eid, ts });
  }
  const sortedDays = Object.keys(dayGroups).map(Number).sort((a, b) => a - b);
  for (const d of sortedDays) {
    dayGroups[d].sort((a, b) =>
      a.ts.period !== b.ts.period ? a.ts.period - b.ts.period
      : (exam_room[a.eid] ?? 0) - (exam_room[b.eid] ?? 0)
    );
  }

  /* ── Emit day groups ── */
  const dateSepStyle = {
    font: FONT_CAL(12, true), fill: FILL("FFC000"),
    alignment: { horizontal: "center" }, border: { ...BORDER_LTB },
  };
  const dateSepEmpty = {
    fill: FILL("FFC000"), border: { ...BORDER_LTB },
  };

  // Data cell style factories
  const dS = (hAlign, wrap = false) => ({
    font: FONT_CAL(11), border: { ...BORDER_ALL },
    alignment: { horizontal: hAlign, vertical: "center", ...(wrap ? { wrapText: true } : {}) },
  });

  for (const day of sortedDays) {
    const sepLabel = hasRealDates
      ? fmtDateTR(addDays(base, day))
      : `[TARİH / DATE] — Day ${day}`;
    const cellDate = hasRealDates
      ? fmtDateTR(addDays(base, day))
      : `[DATE] — Day ${day}`;

    /* Date separator row */
    setCell(ws, 0, R, sepLabel, dateSepStyle);
    for (let c = 1; c <= 6; c++) setCell(ws, c, R, "", dateSepEmpty);
    merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 6 } });
    rowHts[R] = 15.75;
    R++;

    /* Exam rows */
    for (const { eid, ts } of dayGroups[day]) {
      const exam = examMap[eid];
      const room = roomMap[exam_room[eid]];
      const lec  = instrMap[exam?.lecturer_id];
      const invIds = assigned_invigilators[eid] || [];
      const instrName = lec?.name ?? (invIds.length > 0 ? instrMap[invIds[0]]?.name : "") ?? "";

      setCell(ws, 0, R, exam?.code ?? `E${eid}`,                 dS("center", true));
      setCell(ws, 1, R, exam?.name ?? `Exam ${eid}`,             dS("left", true));
      setCell(ws, 2, R, instrName,                                dS("left", true));
      setCell(ws, 3, R, cellDate,                                 dS("center"));
      setCell(ws, 4, R, resolveTime(ts.period, meta),            dS("center"));
      setCell(ws, 5, R, exam?.studentCount ?? "", {
        font: FONT_CAL(11), border: { ...BORDER_ALL },
        alignment: ALIGN_CC,
      });
      setCell(ws, 6, R, room?.label ?? `Room ${exam_room[eid]}`, dS("center"));
      rowHts[R] = 30;
      R++;
    }
  }

  /* ── Unassigned section ── */
  const unassigned = sr.unassigned || [];
  if (unassigned.length > 0) {
    setCell(ws, 0, R, "ATANAMAYAN DERSLER / UNASSIGNED EXAMS", {
      font: FONT_CAL(12, true), fill: FILL("FF9999"),
      alignment: { horizontal: "center" }, border: { ...BORDER_ALL },
    });
    for (let c = 1; c <= 6; c++) setCell(ws, c, R, "", {
      fill: FILL("FF9999"), border: { ...BORDER_ALL },
    });
    merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 6 } });
    rowHts[R] = 20;
    R++;

    for (const eid of unassigned) {
      const exam = examMap[eid];
      const lec = instrMap[exam?.lecturer_id];
      setCell(ws, 0, R, exam?.code ?? `E${eid}`, dS("center", true));
      setCell(ws, 1, R, exam?.name ?? `Exam ${eid}`, dS("left", true));
      setCell(ws, 2, R, lec?.name ?? "", dS("left", true));
      setCell(ws, 3, R, "—", dS("center"));
      setCell(ws, 4, R, "—", dS("center"));
      setCell(ws, 5, R, exam?.studentCount ?? "", { font: FONT_CAL(11), border: { ...BORDER_ALL }, alignment: ALIGN_CC });
      setCell(ws, 6, R, "—", dS("center"));
      rowHts[R] = 24;
      R++;
    }
  }

  /* ── Summary footer ── */
  R++;
  const summary = [
    `Placed: ${placed.length}/${pd.exams.length}`,
    `Objective: ${sr.objective ?? "—"}`,
    `Solve Time: ${sr.solveTime != null ? sr.solveTime.toFixed(2) + "s" : "—"}`,
    `Generated: ${new Date().toLocaleString()}`,
  ].join("  |  ");
  setCell(ws, 0, R, summary, {
    font: FONT_CAL(9), alignment: { horizontal: "left" },
    font: { ...FONT_CAL(9), color: { rgb: "666666" } },
  });
  merges.push({ s: { r: R, c: 0 }, e: { r: R, c: 6 } });
  R++;

  /* ── Worksheet metadata ── */
  ws["!ref"] = `A1:G${R}`;
  ws["!merges"] = merges;
  ws["!cols"] = [
    { wch: 15.1 }, { wch: 34.3 }, { wch: 36.4 },
    { wch: 21.3 }, { wch: 12.7 }, { wch: 12.7 }, { wch: 12.6 },
  ];
  ws["!rows"] = Object.entries(rowHts).reduce((acc, [r, h]) => {
    acc[parseInt(r)] = { hpx: h };
    return acc;
  }, {});

  return ws;
}


/* ────────────────────────────────────────────────────────────
   SHEET 2 — ROOM CAPACITY  (SINIF KAPASİTESİ)
   Row 1: Headers with bg #FFFF00, bold, h=60
   Data:  center/center, thin borders all sides
   Col A-B: Regular classrooms  |  Col D-E: Labs
   ──────────────────────────────────────────────────────────── */

function buildRoomSheet(pd, meta) {
  const rooms = pd.rooms || [];
  const labKw = ["lab", "mlab", "çizim", "drawing"];
  const isLab = (l) => labKw.some((k) => (l || "").toLowerCase().includes(k));

  let regular, labs;
  if (meta?.labRoomIds) {
    const s = new Set(meta.labRoomIds);
    regular = rooms.filter((r) => !s.has(r.id));
    labs = rooms.filter((r) => s.has(r.id));
  } else {
    regular = rooms.filter((r) => !isLab(r.label));
    labs = rooms.filter((r) => isLab(r.label));
    if (labs.length === 0) regular = rooms;
  }

  const ws = {};
  const maxR = Math.max(regular.length, labs.length);

  const hdrStyle = {
    font: FONT_CAL(11, true), fill: FILL("FFFF00"),
    alignment: ALIGN_CC_WRAP, border: { ...BORDER_ALL },
  };
  const cellStyle = {
    font: FONT_CAL(11), alignment: ALIGN_CC, border: { ...BORDER_ALL },
  };

  // Row 0: Headers
  setCell(ws, 0, 0, "Kullanılabilen Derslikler\nAvailable Classrooms", hdrStyle);
  setCell(ws, 1, 0, "Kapasitesi\nCapacity", hdrStyle);
  if (labs.length > 0) {
    setCell(ws, 3, 0, "Bilgisayar Labları ve Çizim Sınıfları\nComputer Labs & Drawing Rooms", hdrStyle);
    setCell(ws, 4, 0, "Kapasitesi\nCapacity", hdrStyle);
  }

  // Data rows
  for (let i = 0; i < maxR; i++) {
    const r = i + 1;
    if (regular[i]) {
      setCell(ws, 0, r, regular[i].label || `R-${regular[i].id}`, cellStyle);
      setCell(ws, 1, r, regular[i].capacity, cellStyle);
    }
    if (labs[i]) {
      setCell(ws, 3, r, labs[i].label || `Lab-${labs[i].id}`, cellStyle);
      setCell(ws, 4, r, labs[i].capacity, cellStyle);
    }
  }

  ws["!ref"] = `A1:${labs.length > 0 ? "E" : "B"}${maxR + 1}`;
  ws["!cols"] = [
    { wch: 23 }, { wch: 10 }, { wch: 3 },
    { wch: 35 }, { wch: 16 },
  ];
  ws["!rows"] = { 0: { hpx: 60 } };

  return ws;
}


/* ────────────────────────────────────────────────────────────
   SHEET 3 — LEAVE DAYS  (İZİN GÜNLERİ)
   Row 1: Merged A1:E1, Times 16, h=38.25
   Row 2: Column headers, Times 16/12, h=31.5
   Data:  Times 10-12, thin borders, h=15.75
   ──────────────────────────────────────────────────────────── */

function buildLeaveSheet(pd, meta, lookups) {
  const ws = {};
  const merges = [];

  const termLabel = meta?.termTR || meta?.term || "[Dönem / Term]";

  // Row 0: Merged header
  setCell(ws, 0, 0, `${termLabel} Akademik Araştırma ve İzin Günleri\nAcademic Research and Leave Days`, {
    font: FONT_TIMES(16), alignment: ALIGN_CC_WRAP,
    border: { bottom: B_THIN, left: B_THIN },
  });
  for (let c = 1; c <= 4; c++) setCell(ws, c, 0, "", {
    border: { bottom: B_THIN },
  });
  merges.push({ s: { r: 0, c: 0 }, e: { r: 0, c: 4 } });

  // Row 1: Column headers
  const hdrS = (sz) => ({
    font: FONT_TIMES(sz), alignment: ALIGN_CC_WRAP, border: { ...BORDER_ALL },
  });
  setCell(ws, 0, 1, "SIRA NO\nNo",          hdrS(12));
  setCell(ws, 1, 1, "UNVAN / AD SOYAD\nTitle / Name", hdrS(16));
  setCell(ws, 2, 1, "İZİN GÜNÜ 1\nLeave Day 1",      hdrS(16));
  setCell(ws, 3, 1, "İZİN GÜNÜ 2\nLeave Day 2",      hdrS(16));
  setCell(ws, 4, 1, "İZİN GÜNÜ 3\nLeave Day 3",      hdrS(16));

  // Timeslot ID → weekday name map for preference parsing
  const tsDay = {};
  for (const ts of pd.timeslots) tsDay[ts.id] = WEEKDAY_LABELS[ts.day % 7];

  const instructors = pd.instructors || [];
  const numS = { font: FONT_TIMES(12), border: { ...BORDER_ALL } };
  const nameS = { font: FONT_TIMES(10), border: { ...BORDER_ALL } };
  const dayS = {
    font: FONT_TIMES(10), border: { ...BORDER_ALL },
    alignment: { horizontal: "left", vertical: "center" },
  };

  for (let i = 0; i < instructors.length; i++) {
    const inst = instructors[i];
    const R = i + 2;

    let leave = [];
    if (meta?.instructorLeave?.[inst.id]) {
      leave = meta.instructorLeave[inst.id];
    } else if (inst.preferences) {
      const unavail = new Set();
      for (const [tsId, avail] of Object.entries(inst.preferences)) {
        if (!avail) {
          const dn = tsDay[parseInt(tsId, 10)];
          if (dn) unavail.add(dn);
        }
      }
      leave = [...unavail];
    }

    setCell(ws, 0, R, i + 1, numS);
    setCell(ws, 1, R, inst.name || `Instructor ${inst.id}`, nameS);
    setCell(ws, 2, R, leave[0] ?? "", dayS);
    setCell(ws, 3, R, leave[1] ?? "", dayS);
    setCell(ws, 4, R, leave[2] ?? "", dayS);
  }

  const totalRows = instructors.length + 2;
  ws["!ref"] = `A1:E${totalRows}`;
  ws["!merges"] = merges;
  ws["!cols"] = [
    { wch: 6.4 }, { wch: 47.7 }, { wch: 32.7 }, { wch: 30.4 }, { wch: 30.4 },
  ];
  ws["!rows"] = {
    0: { hpx: 38.25 },
    1: { hpx: 31.5 },
    ...Object.fromEntries(
      Array.from({ length: instructors.length }, (_, i) => [i + 2, { hpx: 15.75 }])
    ),
  };

  return ws;
}


/* ────────────────────────────────────────────────────────────
   MAIN EXPORT FUNCTION
   ──────────────────────────────────────────────────────────── */

/**
 * @param {object} problemData  — { exams[], timeslots[], rooms[], instructors[] }
 * @param {object} solverResult — { solution, unassigned[], objective, solveTime, ... }
 * @param {string} datasetName  — used in filename
 * @param {object} [metadata]   — optional institutional details (see JSDoc below)
 */
export function exportScheduleToExcel(
  problemData,
  solverResult,
  datasetName = "schedule",
  metadata = null,
) {
  if (!problemData || !solverResult?.solution) {
    console.warn("exportScheduleToExcel: missing data, aborting.");
    return;
  }

  const lookups = buildLookups(problemData);

  const ws1 = buildScheduleSheet(problemData, solverResult, metadata, lookups);
  const ws2 = buildRoomSheet(problemData, metadata);
  const ws3 = buildLeaveSheet(problemData, metadata, lookups);

  const sn1 = metadata?.scheduleType
    ? metadata.scheduleType.toUpperCase().slice(0, 31)
    : "EXAM SCHEDULE";

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws1, sn1);
  XLSX.utils.book_append_sheet(wb, ws2, "SINIF KAPASİTESİ");
  XLSX.utils.book_append_sheet(wb, ws3, "İZİN GÜNLERİ");

  const ts = new Date().toISOString().slice(0, 10);
  const safe = datasetName.replace(/[^a-zA-Z0-9_-]/g, "_");
  XLSX.writeFile(wb, `exam_schedule_${safe}_${ts}.xlsx`);
}