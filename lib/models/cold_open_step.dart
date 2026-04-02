enum ColdOpenStepType {
  text,
  chat,
  receipt,
  image,
  journal,
  cliffhanger,
}

class ColdOpenStep {
  final ColdOpenStepType type;
  final String? sender;
  final String? body;
  final String? title;
  final bool isProtagonist;
  final Duration displayDuration;

  const ColdOpenStep({
    required this.type,
    this.sender,
    this.body,
    this.title,
    this.isProtagonist = false,
    this.displayDuration = const Duration(seconds: 4),
  });
}

/// The curated cold-open script: a mini thriller in ~60 seconds.
const List<ColdOpenStep> defaultColdOpenScript = [
  ColdOpenStep(
    type: ColdOpenStepType.text,
    body: 'INTERCEPTED SIGNAL',
    title: 'RECOVERED DEVICE — CASE #4471',
    displayDuration: Duration(seconds: 3),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.text,
    body: 'The following artifacts were extracted from a phone recovered at the scene.',
    displayDuration: Duration(seconds: 4),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.chat,
    sender: 'Unknown',
    body: 'Are you still at the hotel?',
    displayDuration: Duration(seconds: 3),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.chat,
    sender: 'Me',
    body: 'Left an hour ago. Don\'t call me again. They already know.',
    isProtagonist: true,
    displayDuration: Duration(seconds: 4),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.receipt,
    title: 'TRANSACTION RECORD',
    body: 'Hardware store — \$47.89 — "rope, tarp, duct tape"',
    displayDuration: Duration(seconds: 4),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.journal,
    title: 'Journal — 11:42 PM',
    body: 'I keep telling myself it was the right thing to do. But the blood won\'t come off my hands.',
    displayDuration: Duration(seconds: 5),
  ),
  ColdOpenStep(
    type: ColdOpenStepType.cliffhanger,
    body: 'New entry unlocks tonight.',
    title: 'SIGNAL LOST',
    displayDuration: Duration(seconds: 5),
  ),
];
