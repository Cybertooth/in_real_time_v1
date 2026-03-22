import 'package:cloud_firestore/cloud_firestore.dart';

DateTime _readUnlockTimestamp(Map<String, dynamic> data) {
  final raw = data['unlockTimestamp'];
  if (raw is Timestamp) return raw.toDate();
  if (raw is DateTime) return raw;
  return DateTime.now();
}

int _readTimeOffsetMinutes(Map<String, dynamic> data) {
  final raw = data['timeOffsetMinutes'] ?? data['time_offset_minutes'];
  if (raw is int) return raw;
  if (raw is num) return raw.toInt();
  return 0;
}

/// Base class for all time-gated story content.
abstract class StoryItem {
  final String id;
  final DateTime unlockTimestamp;
  final int timeOffsetMinutes;
  final String? imageUrl;
  final bool isPasswordLocked;
  final String? unlockPassword;

  StoryItem({
    required this.id, 
    required this.unlockTimestamp,
    this.timeOffsetMinutes = 0,
    this.imageUrl,
    this.isPasswordLocked = false,
    this.unlockPassword,
  });

  bool get isLocked => DateTime.now().isBefore(unlockTimestamp);

  /// Content type label used in the unified timeline feed.
  String get contentType;
}

// ---------------------------------------------------------------------------
// Journal
// ---------------------------------------------------------------------------
class Journal extends StoryItem {
  final String title;
  final String body;

  Journal({
    required this.title,
    required this.body,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'journal';

  factory Journal.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return Journal(
      id: doc.id,
      title: data['title'] ?? '',
      body: data['body'] ?? '',
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Chat (1‑on‑1 message)
// ---------------------------------------------------------------------------
class Chat extends StoryItem {
  final String senderId;
  final String text;
  final bool isProtagonist;

  Chat({
    required this.senderId,
    required this.text,
    required this.isProtagonist,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'chat';

  factory Chat.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return Chat(
      id: doc.id,
      senderId: data['senderId'] ?? '',
      text: data['text'] ?? '',
      isProtagonist: data['isProtagonist'] ?? false,
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Email
// ---------------------------------------------------------------------------
class Email extends StoryItem {
  final String sender;
  final String subject;
  final String body;

  Email({
    required this.sender,
    required this.subject,
    required this.body,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'email';

  factory Email.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return Email(
      id: doc.id,
      sender: data['sender'] ?? '',
      subject: data['subject'] ?? '',
      body: data['body'] ?? '',
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Receipt
// ---------------------------------------------------------------------------
class Receipt extends StoryItem {
  final String merchantName;
  final double amount;
  final String description;

  Receipt({
    required this.merchantName,
    required this.amount,
    required this.description,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'receipt';

  factory Receipt.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return Receipt(
      id: doc.id,
      merchantName: data['merchantName'] ?? '',
      amount: (data['amount'] as num).toDouble(),
      description: data['description'] ?? '',
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Voice Note
// ---------------------------------------------------------------------------
class VoiceNote extends StoryItem {
  final String speaker;
  final String transcript;
  final String? audioUrl;
  final String? voiceId;

  VoiceNote({
    required this.speaker,
    required this.transcript,
    this.audioUrl,
    this.voiceId,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'voice_note';

  factory VoiceNote.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return VoiceNote(
      id: doc.id,
      speaker: data['speaker'] ?? '',
      transcript: data['transcript'] ?? '',
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      audioUrl: data['audioUrl'] as String? ?? data['audio_url'] as String?,
      voiceId: data['voiceId'] as String? ?? data['voice_id'] as String?,
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Social Post
// ---------------------------------------------------------------------------
class SocialPost extends StoryItem {
  final String platform; // "instagram", "twitter", etc.
  final String author;
  final String handle;
  final String content;
  final int likes;
  final int comments;

  SocialPost({
    required this.platform,
    required this.author,
    required this.handle,
    required this.content,
    required this.likes,
    required this.comments,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'social_post';

  factory SocialPost.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return SocialPost(
      id: doc.id,
      platform: data['platform'] ?? 'twitter',
      author: data['author'] ?? '',
      handle: data['handle'] ?? '',
      content: data['content'] ?? '',
      likes: (data['likes'] as num?)?.toInt() ?? 0,
      comments: (data['comments'] as num?)?.toInt() ?? 0,
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Phone Call  (with nested transcript lines)
// ---------------------------------------------------------------------------
class PhoneCallLine {
  final String speaker;
  final String text;

  PhoneCallLine({required this.speaker, required this.text});

  factory PhoneCallLine.fromMap(Map<String, dynamic> m) {
    return PhoneCallLine(
      speaker: m['speaker'] ?? '',
      text: m['text'] ?? '',
    );
  }
}

class PhoneCall extends StoryItem {
  final String caller;
  final String receiver;
  final int durationSeconds;
  final List<PhoneCallLine> lines;

  PhoneCall({
    required this.caller,
    required this.receiver,
    required this.durationSeconds,
    required this.lines,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'phone_call';

  factory PhoneCall.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final rawLines = data['lines'] as List<dynamic>? ?? [];
    final unlockAt = _readUnlockTimestamp(data);
    return PhoneCall(
      id: doc.id,
      caller: data['caller'] ?? '',
      receiver: data['receiver'] ?? '',
      durationSeconds: (data['duration_seconds'] as num?)?.toInt() ?? 0,
      lines: rawLines
          .map((l) => PhoneCallLine.fromMap(Map<String, dynamic>.from(l)))
          .toList(),
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}

// ---------------------------------------------------------------------------
// Gallery Photo  (standalone image: atmospheric, diegetic, or document)
// ---------------------------------------------------------------------------
class GalleryPhoto extends StoryItem {
  final String tier; // "atmospheric" | "diegetic" | "document"
  final String subject;
  final String? caption;

  GalleryPhoto({
    required this.tier,
    required this.subject,
    this.caption,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'gallery_photo';

  factory GalleryPhoto.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final unlockAt = _readUnlockTimestamp(data);
    return GalleryPhoto(
      id: doc.id,
      tier: data['tier'] ?? 'diegetic',
      subject: data['subject'] ?? '',
      caption: data['caption'] as String?,
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'] as String?,
    );
  }
}

// ---------------------------------------------------------------------------
// Group Chat Thread  (with nested messages)
// ---------------------------------------------------------------------------
class GroupChatMessage {
  final String sender;
  final String text;

  GroupChatMessage({required this.sender, required this.text});

  factory GroupChatMessage.fromMap(Map<String, dynamic> m) {
    return GroupChatMessage(
      sender: m['sender'] ?? '',
      text: m['text'] ?? '',
    );
  }
}

class GroupChatThread extends StoryItem {
  final String platform; // "whatsapp", "telegram", etc.
  final String groupName;
  final List<String> members;
  final List<GroupChatMessage> messages;

  GroupChatThread({
    required this.platform,
    required this.groupName,
    required this.members,
    required this.messages,
    required super.unlockTimestamp,
    super.id = '',
    super.timeOffsetMinutes = 0,
    super.imageUrl,
    super.isPasswordLocked = false,
    super.unlockPassword,
  });

  @override
  String get contentType => 'group_chat';

  factory GroupChatThread.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    final rawMessages = data['messages'] as List<dynamic>? ?? [];
    final rawMembers = data['members'] as List<dynamic>? ?? [];
    final unlockAt = _readUnlockTimestamp(data);
    return GroupChatThread(
      id: doc.id,
      platform: data['platform'] ?? 'whatsapp',
      groupName: data['group_name'] ?? '',
      members: rawMembers.map((m) => m.toString()).toList(),
      messages: rawMessages
          .map((m) => GroupChatMessage.fromMap(Map<String, dynamic>.from(m)))
          .toList(),
      unlockTimestamp: unlockAt,
      timeOffsetMinutes: _readTimeOffsetMinutes(data),
      imageUrl: data['imageUrl'],
      isPasswordLocked: data['is_locked'] ?? false,
      unlockPassword: data['unlock_password'],
    );
  }
}
