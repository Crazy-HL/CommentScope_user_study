export const PARTICIPANT_IDS = Object.freeze([
  "P01", "P02", "P03", "P04", "P05", "P06",
  "P07", "P08", "P09", "P10", "P11", "P12",
  "P13", "P14", "P15", "P16", "P17", "P18",
  "P19", "P20", "P21", "P22", "P23", "P24"
]);

// Internal codes are never rendered as participant-facing labels.
export const CONDITION_CODES = Object.freeze(["TE", "CS", "SE", "BL"]);
export const PREFERENCE_OPTIONS = Object.freeze([
  { value: "TE", label: "界面 1（评论集中显示）" },
  { value: "CS", label: "界面 2（点击标记查看评论）" },
  { value: "SE", label: "界面 3（评论紧随相关句子）" },
  { value: "BL", label: "界面 4（评论穿插在正文之间）" }
]);

export const QUESTION_GROUPS = Object.freeze(["cra", "aca", "ctia", "location"]);
export const NEXT_STAGE = Object.freeze({
  cra: "aca",
  aca: "ctia",
  ctia: "location",
  location: "workload"
});

export const STAGE_TITLES = Object.freeze({
  instruction: "实验说明",
  reading: "自然阅读",
  cra: "评论识别",
  aca: "文章理解",
  ctia: "评论理解",
  location: "信息定位",
  workload: "阅读体验评价",
  preference: "界面偏好",
  interview: "使用体验反馈",
  complete: "实验完成"
});

export const INTERVIEW_QUESTIONS = Object.freeze([
  "在四种评论展示界面中，你最喜欢哪一种？为什么？",
  "哪一种评论展示界面最影响你的连续阅读？请描述具体情况。",
  "你在查找评论与正文关系时采用了什么方法？",
  "如果可以改进这些评论展示界面，你最希望修改什么？"
]);
