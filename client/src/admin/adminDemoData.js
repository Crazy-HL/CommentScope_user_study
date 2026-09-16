const CONDITIONS = ["TE", "CS", "SE", "BL"];
const COLOR_MAP_NAME = "coolwarm";
const CONDITION_COLORS = {
  TE: "#3b4cc0",
  CS: "#7b9ff9",
  SE: "#f39c7d",
  BL: "#b40426"
};

function clamp(value, lower, upper) {
  return Math.max(lower, Math.min(upper, value));
}

function quantize(value, itemCount) {
  return clamp(Math.round(value * itemCount) / itemCount, 0, 1);
}

function makeMatrix(bases, spread, itemCount = null) {
  return Array.from({ length: 24 }, (_, participantIndex) => CONDITIONS.map((condition, conditionIndex) => {
    const wave = Math.sin((participantIndex + 1) * 1.73 + conditionIndex * 0.91) * spread;
    const secondaryWave = Math.cos((participantIndex + 2) * 0.67 + conditionIndex) * spread * 0.42;
    const value = bases[conditionIndex] + wave + secondaryWave;
    return itemCount ? quantize(value, itemCount) : Number(value.toFixed(2));
  }));
}

// Stable, in-memory preview data. It is intentionally not sent to the server or saved in SQLite.
export const DEMO_CONDITIONS = CONDITIONS;
export const DEMO_COLOR_MAP_NAME = COLOR_MAP_NAME;
export const DEMO_CONDITION_COLORS = CONDITION_COLORS;
export const DEMO_ACADEMIC_DATA = {
  overallTime: makeMatrix([118000, 132000, 109000, 148000], 17000),
  overallAccuracy: makeMatrix([0.78, 0.73, 0.84, 0.68], 0.16, 4),
  taskAccuracy: {
    "Article Comprehension": makeMatrix([0.84, 0.80, 0.86, 0.77], 0.12, 2),
    "Comment-Linked Comprehension": makeMatrix([0.76, 0.70, 0.85, 0.63], 0.18, 2),
    "Comment Location": makeMatrix([0.81, 0.75, 0.88, 0.66], 0.16, 2)
  }
};

export function buildAcademicDataFromSummary(summary) {
  const metrics = summary?.metrics || {};
  const conditionObservations = metricName => CONDITIONS.map(condition => metrics[metricName]?.[condition]?.observations || []);
  const toRows = series => {
    const length = Math.max(0, ...series.map(values => values.length));
    return Array.from({ length }, (_, rowIndex) => CONDITIONS.map((_, conditionIndex) => series[conditionIndex][rowIndex] ?? null));
  };
  const taskNames = ["ACA", "CTIA", "CLA"];
  const taskAccuracy = {
    "Article Comprehension": toRows(conditionObservations("ACA")),
    "Comment-Linked Comprehension": toRows(conditionObservations("CTIA")),
    "Comment Location": toRows(conditionObservations("CLA"))
  };
  const accuracySeries = CONDITIONS.map(condition => {
    const taskSeries = taskNames.map(metricName => metrics[metricName]?.[condition]?.observations || []);
    const length = Math.max(0, ...taskSeries.map(values => values.length));
    return Array.from({ length }, (_, rowIndex) => {
      const values = taskSeries.map(values => values[rowIndex]).filter(value => value != null).map(Number);
      return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
    });
  });
  return {
    overallTime: toRows(conditionObservations("Initial Reading Time")),
    overallAccuracy: toRows(accuracySeries),
    taskAccuracy
  };
}

function makeMetricSeries(bases, spread, itemCount = null) {
  const matrix = makeMatrix(bases, spread, itemCount);
  return Object.fromEntries(CONDITIONS.map((condition, conditionIndex) => [condition, {
    n: matrix.length,
    observations: matrix.map(row => row[conditionIndex])
  }]));
}

// Additional deterministic preview series used by the full academic analysis page.
export const DEMO_ACADEMIC_METRICS = {
  CTIA: makeMetricSeries([0.78, 0.73, 0.86, 0.68], 0.14, 2),
  CTIRT: makeMetricSeries([18400, 21900, 17100, 24600], 4200),
  CRA: makeMetricSeries([0.74, 0.69, 0.80, 0.64], 0.16, 4),
  ACA: makeMetricSeries([0.84, 0.80, 0.87, 0.77], 0.12, 2),
  CLA: makeMetricSeries([0.80, 0.75, 0.86, 0.67], 0.16, 2),
  CLT: makeMetricSeries([15600, 18500, 14300, 21100], 3800),
  "Initial Reading Time": makeMetricSeries([118000, 132000, 109000, 148000], 17000),
  NSD: makeMetricSeries([2.15, 2.42, 1.94, 2.76], 0.55),
  "Scroll Events": makeMetricSeries([18, 22, 16, 26], 5),
  "Total Scroll Distance": makeMetricSeries([8100, 9200, 7400, 10400], 1900),
  "Max Scroll Y": makeMetricSeries([5900, 6200, 5600, 6800], 950),
  "Comment Interaction Count": makeMetricSeries([4.2, 5.8, 3.7, 2.6], 1.6),
  "Comment Click Count": makeMetricSeries([0.8, 3.4, 1.8, 0.6], 1.2),
  "Comment Open Count": makeMetricSeries([0.2, 2.8, 1.4, 0.1], 1.0),
  "Comment Close Count": makeMetricSeries([0.1, 2.3, 1.1, 0.1], 0.9),
  "Paragraph Toggle Count": makeMetricSeries([1.7, 0.4, 1.2, 0.1], 0.8),
  RC: makeMetricSeries([5.8, 5.2, 6.0, 4.7], 0.75),
  CA: makeMetricSeries([5.2, 5.8, 6.1, 4.4], 0.8),
  "NASA-TLX Mental Demand": makeMetricSeries([3.6, 4.3, 3.1, 5.1], 0.9),
  "NASA-TLX Physical Demand": makeMetricSeries([2.2, 2.6, 1.8, 2.9], 0.6),
  "NASA-TLX Temporal Demand": makeMetricSeries([2.8, 3.5, 2.5, 4.1], 0.7),
  "NASA-TLX Performance": makeMetricSeries([5.4, 4.9, 5.8, 4.3], 0.8),
  "NASA-TLX Effort": makeMetricSeries([3.4, 4.2, 3.0, 4.8], 0.8),
  "NASA-TLX Frustration": makeMetricSeries([2.4, 3.2, 2.0, 4.0], 0.7)
};

export const DEMO_PREFERENCE_DATA = {
  meanRank: makeMetricSeries([2.45, 2.70, 1.65, 3.20], 0.48),
  firstPlaceShare: makeMetricSeries([0.22, 0.18, 0.43, 0.10], 0.12, null)
};

export function buildMetricSeriesFromSummary(summary, metricName) {
  const metrics = summary?.metrics || {};
  return Object.fromEntries(CONDITIONS.map(condition => [condition, metrics[metricName]?.[condition] || { observations: [] }]));
}

export function buildPreferenceSeriesFromSummary(summary) {
  const preference = summary?.preference || {};
  const rank = Object.fromEntries(CONDITIONS.map(condition => [condition, preference.rank?.[condition] || { observations: [] }]));
  const submitted = Number(preference.submitted || 0);
  const firstPlaceShare = Object.fromEntries(CONDITIONS.map(condition => [condition, {
    observations: submitted ? [Number(preference.rank_one?.[condition] || 0) / submitted] : []
  }]));
  return { meanRank: rank, firstPlaceShare };
}


export const DEMO_PARTICIPANTS = Array.from({ length: 24 }, (_, index) => `P${String(index + 1).padStart(2, "0")}`);
export const DEMO_ARTICLES = ["A02", "A03", "A04", "A07"];

function summarizeDemoValues(values) {
  const cleaned = values.filter(value => value != null).map(Number);
  if (!cleaned.length) return { n: 0, mean: null, median: null, stddev: null, ci95: null, observations: [] };
  const mean = cleaned.reduce((sum, value) => sum + value, 0) / cleaned.length;
  const ordered = [...cleaned].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  const median = ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
  const variance = cleaned.length > 1
    ? cleaned.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (cleaned.length - 1)
    : 0;
  const stddev = Math.sqrt(variance);
  return { n: cleaned.length, mean, median, stddev, ci95: cleaned.length > 1 ? 1.96 * stddev / Math.sqrt(cleaned.length) : 0, observations: cleaned };
}

const DEMO_SEQUENCE_GROUP_INDEX = {
  "01-02-03-04": 0,
  "02-03-04-01": 1,
  "03-04-01-02": 2,
  "04-01-02-03": 3,
};

const DEMO_ARTICLE_PLANS = [
  [
    { articleId: "A02", condition: "TE" },
    { articleId: "A03", condition: "CS" },
    { articleId: "A04", condition: "SE" },
    { articleId: "A07", condition: "BL" },
  ],
  [
    { articleId: "A03", condition: "SE" },
    { articleId: "A04", condition: "BL" },
    { articleId: "A07", condition: "TE" },
    { articleId: "A02", condition: "CS" },
  ],
  [
    { articleId: "A04", condition: "TE" },
    { articleId: "A07", condition: "CS" },
    { articleId: "A02", condition: "SE" },
    { articleId: "A03", condition: "BL" },
  ],
  [
    { articleId: "A07", condition: "SE" },
    { articleId: "A02", condition: "TE" },
    { articleId: "A03", condition: "CS" },
    { articleId: "A04", condition: "BL" },
  ],
];

function demoParticipantIndexesForSequence(sequence) {
  const groupIndex = DEMO_SEQUENCE_GROUP_INDEX[sequence];
  return groupIndex == null ? Array.from({ length: 24 }, (_, index) => index) : Array.from({ length: 6 }, (_, index) => groupIndex * 6 + index);
}

function demoArticlePlanForParticipant(participantIndex) {
  return DEMO_ARTICLE_PLANS[Math.floor(participantIndex / 6)] || DEMO_ARTICLE_PLANS[0];
}

function demoSampleIndexes(filters = {}) {
  const participantIndex = filters.participant_id ? DEMO_PARTICIPANTS.indexOf(filters.participant_id) : -1;
  let indexes = participantIndex >= 0 ? [participantIndex] : demoParticipantIndexesForSequence(filters.article_sequence);
  if (participantIndex >= 0 && filters.article_sequence && !demoParticipantIndexesForSequence(filters.article_sequence).includes(participantIndex)) indexes = [];
  // Every participant reads all four articles. Article and position filters
  // narrow article-session aggregates, but do not remove participants from the
  // participant-level scope used for progress and preference summaries.
  if (filters.status === "completed") indexes = indexes.slice(0, Math.ceil(indexes.length * 0.75));
  if (filters.status === "active") indexes = indexes.slice(Math.ceil(indexes.length * 0.75));
  return indexes;
}

function demoMetricMap(filters) {
  const indexes = demoSampleIndexes(filters);
  const metrics = {};
  for (const [name, series] of Object.entries(DEMO_ACADEMIC_METRICS)) {
    metrics[name] = {};
    for (const condition of CONDITIONS) {
      const source = series[condition]?.observations || [];
      metrics[name][condition] = summarizeDemoValues(indexes.map(index => source[index % source.length]));
    }
  }
  return metrics;
}

function demoParticipantCount(filters) {
  return demoSampleIndexes(filters).length;
}

function demoParticipantOverview(filters = {}) {
  const participantIndex = filters.participant_id ? DEMO_PARTICIPANTS.indexOf(filters.participant_id) : -1;
  let indexes = participantIndex >= 0
    ? [participantIndex]
    : demoParticipantIndexesForSequence(filters.article_sequence);
  if (participantIndex >= 0 && filters.article_sequence && !indexes.includes(participantIndex)) indexes = [];

  const completedCutoff = Math.ceil(indexes.length * 0.75);
  if (filters.status === "completed") indexes = indexes.slice(0, completedCutoff);
  if (filters.status === "active") indexes = indexes.slice(completedCutoff);

  const sequenceForIndex = index => Object.keys(DEMO_SEQUENCE_GROUP_INDEX).find(
    sequence => DEMO_SEQUENCE_GROUP_INDEX[sequence] === Math.floor(index / 6)
  ) || "01-02-03-04";
  const hasSessionFilter = Boolean(filters.article_id || filters.condition || filters.article_order);
  const expectedSessions = hasSessionFilter ? 1 : 4;

  return indexes.map((index, scopedIndex) => {
    const completed = scopedIndex < completedCutoff;
    const active = !completed;
    const articleSessionsCompleted = completed
      ? expectedSessions
      : Math.min(expectedSessions - 1, Math.max(0, Math.floor(expectedSessions / 2)));
    const articleSessionsStarted = active ? Math.max(articleSessionsCompleted, 1) : articleSessionsCompleted;
    const responsesCount = articleSessionsCompleted * 10;
    const preferenceSubmitted = completed;
    const reasonSubmitted = preferenceSubmitted && index % 6 !== 5;
    const interviewSubmitted = preferenceSubmitted && index % 5 !== 4;
    return {
      participant_id: DEMO_PARTICIPANTS[index],
      group_id: `G${Math.floor(index / 6) + 1}`,
      article_sequence: sequenceForIndex(index),
      session_status: completed ? "completed" : "active",
      article_sessions_expected: expectedSessions,
      article_sessions_started: articleSessionsStarted,
      article_sessions_completed: articleSessionsCompleted,
      responses_count: responsesCount,
      surveys_count: articleSessionsCompleted,
      preference_submitted: preferenceSubmitted,
      preference_reason_submitted: reasonSubmitted,
      interview_submitted: interviewSubmitted,
      last_seen_at: completed || active ? `2026-09-14T09:${String(10 + index).padStart(2, "0")}:00.000Z` : null,
    };
  });
}

function buildDemoParticipantDetails(filters = {}) {
  const participantIndex = DEMO_PARTICIPANTS.indexOf(filters.participant_id);
  if (participantIndex < 0) return { participant_details: [], participant_tasks: [] };
  const sessionId = `demo-session-${filters.participant_id}`;
  // Participant detail is an explicit whole-participant view. It deliberately
  // ignores article/condition/position/status filters and always returns all
  // four blocks, in the participant's assigned order.
  const slots = demoArticlePlanForParticipant(participantIndex);
  const participantDetails = slots.map((slot, slotIndex) => {
    const articleOrder = slotIndex + 1;
    const active = (participantIndex + slotIndex) % 5 === 4;
    const responseGroups = {
      cra: Array.from({ length: 4 }, (_, index) => ({ question_type: "cra", question_id: `cra-${index + 1}`, selected_option: index % 3 ? "出现过" : "未出现过", correct: index !== 3, elapsed_ms: 850 + index * 130, option_click_count: 1 + (index % 2), option_change_count: index % 2, scroll_event_count: 0, total_scroll_distance_px: 0, max_scroll_y: 0 })),
      aca: Array.from({ length: 2 }, (_, index) => ({ question_type: "aca", question_id: `aca-${index + 1}`, selected_option: "A", correct: index === 0, elapsed_ms: 1100 + index * 180, option_click_count: 1, option_change_count: 0, scroll_event_count: 0, total_scroll_distance_px: 0, max_scroll_y: 0 })),
      cti: Array.from({ length: 2 }, (_, index) => ({ question_type: "cti", question_id: `cti-${index + 1}`, selected_option: "支持", correct: index === 0, elapsed_ms: 1700 + index * 240, option_click_count: 1, option_change_count: 0, scroll_event_count: 0, total_scroll_distance_px: 0, max_scroll_y: 0 })),
      location: Array.from({ length: 2 }, (_, index) => ({ question_type: "location", question_id: `location-${index + 1}`, selected_option: "段落 1", correct: true, elapsed_ms: 1450 + index * 210, option_click_count: 1, option_change_count: 0, scroll_event_count: 0, total_scroll_distance_px: 0, max_scroll_y: 0 })),
    };
    return {
      session_id: sessionId, participant_id: filters.participant_id, article_order: articleOrder, article_id: slot.articleId, condition: slot.condition, status: active ? "active" : "completed",
      initial_reading_time_ms: 108000 + slotIndex * 7000, normalized_scroll_distance: 1.4 + slotIndex * .18, scroll_event_count: 18 + slotIndex * 2, total_scroll_distance_px: 7200 + slotIndex * 640, max_scroll_y: 5600 + slotIndex * 240,
      comment_interaction_count: 2 + slotIndex, comment_click_count: slot.condition === "CS" ? 4 : 1, comment_open_count: slot.condition === "CS" ? 2 : 0, comment_close_count: slot.condition === "CS" ? 2 : 0, paragraph_toggle_count: slot.condition === "TE" ? 2 : 0,
      reading_start_time: `2026-09-14T09:0${slotIndex}:00.000Z`, reading_end_time: `2026-09-14T09:0${slotIndex + 2}:00.000Z`, responses: responseGroups, responses_total: 10,
      CRA: .75, ACA: .5, CTIA: .5, CTIRT: 1820, CLA: 1, CLT: 1555, workload: { mental_demand: 38 + slotIndex * 3, physical_demand: 18, temporal_demand: 25, performance: 72, effort: 41 + slotIndex * 2, frustration: 20, reading_continuity: 5 + (slotIndex % 2), comment_accessibility: 5 + (slotIndex === 1 ? 1 : 0) },
      events: [{ event_row_id: `${slotIndex}-1`, client_occurred_at: `2026-09-14T09:0${slotIndex}:12.000Z`, event_type: "comment_click", stage: "reading", question_id: null, payload: { comment_id: `C0${slotIndex + 1}` } }],
    };
  });
  const participantTasks = [{
    session_id: sessionId, participant_id: filters.participant_id, mode: "formal", status: participantDetails.every(detail => detail.status === "completed") ? "completed" : "active",
    started_at: "2026-09-14T09:00:00.000Z", last_seen_at: "2026-09-14T09:30:00.000Z", completed_at: participantDetails.every(detail => detail.status === "completed") ? "2026-09-14T09:30:00.000Z" : null,
    preference: { ranking: ["SE", "TE", "CS", "BL"], preferred_condition: "SE", reason: "评论和正文的关联比较容易理解。", submitted_at: "2026-09-14T09:40:00.000Z" },
    interview: { answers: { q1: "SE 最容易理解评论对应的位置。", q2: "BL 对连续阅读影响最小。", q3: "TE 有时会让我分心。", q4: "我会选择 SE。" }, started_at: "2026-09-14T09:41:00.000Z", submitted_at: "2026-09-14T09:51:00.000Z" },
  }];
  return { participant_details: participantDetails, participant_tasks: participantTasks };
}

// Full summary-shaped preview data for the ordinary overview page. It remains in memory
// and is never sent to the API or written to SQLite.
export const DEMO_OVERVIEW_SUMMARY = buildDemoOverviewSummary({});

export function buildDemoOverviewSummary(filters = {}) {
  const participants = demoParticipantCount(filters);
  const hasSessionFilter = Boolean(filters.article_id || filters.condition || filters.article_order);
  const expectedSessions = participants * (hasSessionFilter ? 1 : 4);
  const completedSessions = filters.status === "active" ? Math.floor(expectedSessions * 0.25) : Math.ceil(expectedSessions * 0.75);
  const completedParticipants = filters.status === "active" ? 0 : Math.ceil(participants * 0.75);
  const activeParticipants = filters.status === "completed" ? 0 : Math.max(0, participants - completedParticipants);
  const participantTasksSubmitted = filters.status === "active" ? activeParticipants : completedParticipants;
  const responseCount = completedSessions * 10;
  const scopedParticipantIndexes = demoSampleIndexes(filters);
  const preferenceRank = Object.fromEntries(CONDITIONS.map((condition, conditionIndex) => {
    const values = scopedParticipantIndexes.map(index => DEMO_PREFERENCE_DATA.meanRank[condition].observations[index % 24]);
    return [condition, summarizeDemoValues(values)];
  }));
  const rankOne = { TE: 5, CS: 4, SE: 9, BL: 0 };
  const rankFour = { TE: 3, CS: 4, SE: 1, BL: 10 };
  const preferredCondition = { TE: 5, CS: 4, SE: 9, BL: 0 };
  const scalePreference = values => Object.fromEntries(CONDITIONS.map(condition => [condition, Math.round(values[condition] * participantTasksSubmitted / 18)]));
  const metrics = demoMetricMap(filters);
  return {
    last_updated_at: "模拟数据预览",
    overview: {
      expected_participants: 24,
      participants_started: participants,
      participants_completed: completedParticipants,
      participants_active: activeParticipants,
      article_sessions_expected: expectedSessions,
      article_sessions_started: expectedSessions,
      article_sessions_completed: completedSessions,
      responses: { total: responseCount, cra: completedSessions * 4, aca: completedSessions * 2, cti: completedSessions * 2, location: completedSessions * 2 },
      surveys: completedSessions,
      surveys_expected: expectedSessions,
      preferences: participantTasksSubmitted,
      preference_submitted: participantTasksSubmitted,
      preference_reason_submitted: Math.max(0, participantTasksSubmitted - 2),
      preferences_expected: 24,
      preference_reasons_expected: 24,
      interviews: Math.max(0, participantTasksSubmitted - 4),
      interviews_expected: 24,
    },
    metrics,
    participant_overview: demoParticipantOverview(filters),
    preference: {
      rank: preferenceRank,
      rank_one: scalePreference(rankOne),
      rank_four: scalePreference(rankFour),
      preferred_condition: scalePreference(preferredCondition),
      submitted: participantTasksSubmitted,
      reason_submitted: Math.max(0, participantTasksSubmitted - 2),
    },
    ...buildDemoParticipantDetails(filters),
    filter_options: {
      participants: DEMO_PARTICIPANTS,
      articles: DEMO_ARTICLES,
      conditions: CONDITIONS,
      article_orders: [1, 2, 3, 4],
      article_sequences: ["01-02-03-04", "02-03-04-01", "03-04-01-02", "04-01-02-03"],
    },
  };
}
