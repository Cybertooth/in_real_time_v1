import 'package:flutter_test/flutter_test.dart';
import 'package:in_real_time_v1/models/story_item.dart';

void main() {
  // ── Journal ──────────────────────────────────────────────
  group('Journal', () {
    test('isLocked returns true if unlockTimestamp is in the future', () {
      final futureTime = DateTime.now().add(const Duration(hours: 1));
      final journal = Journal(title: 'Test', body: 'Body', unlockTimestamp: futureTime);
      expect(journal.isLocked, isTrue);
      expect(journal.contentType, 'journal');
    });

    test('isLocked returns false if unlockTimestamp is in the past', () {
      final pastTime = DateTime.now().subtract(const Duration(hours: 1));
      final journal = Journal(title: 'Test', body: 'Body', unlockTimestamp: pastTime);
      expect(journal.isLocked, isFalse);
    });
  });

  // ── Chat ─────────────────────────────────────────────────
  group('Chat', () {
    test('Chat handles protagonist flag correctly', () {
      final pastTime = DateTime.now().subtract(const Duration(minutes: 5));
      final chat = Chat(senderId: 'Alex', text: 'Hello', isProtagonist: true, unlockTimestamp: pastTime);
      expect(chat.isProtagonist, isTrue);
      expect(chat.isLocked, isFalse);
      expect(chat.contentType, 'chat');
    });
  });

  // ── VoiceNote ────────────────────────────────────────────
  group('VoiceNote', () {
    test('VoiceNote stores speaker and transcript', () {
      final t = DateTime.now();
      final vn = VoiceNote(speaker: 'Asha', transcript: 'I saw it again.', unlockTimestamp: t);
      expect(vn.speaker, 'Asha');
      expect(vn.transcript, 'I saw it again.');
      expect(vn.contentType, 'voice_note');
    });
  });

  // ── SocialPost ───────────────────────────────────────────
  group('SocialPost', () {
    test('SocialPost stores engagement metrics', () {
      final t = DateTime.now();
      final post = SocialPost(
        platform: 'instagram',
        author: 'Eve',
        handle: 'eve_x',
        content: 'Who is watching?',
        likes: 42,
        comments: 7,
        unlockTimestamp: t,
      );
      expect(post.platform, 'instagram');
      expect(post.likes, 42);
      expect(post.contentType, 'social_post');
    });
  });

  // ── PhoneCall ────────────────────────────────────────────
  group('PhoneCall', () {
    test('PhoneCall stores lines', () {
      final t = DateTime.now();
      final call = PhoneCall(
        caller: 'Alex',
        receiver: 'Boss',
        durationSeconds: 120,
        lines: [
          PhoneCallLine(speaker: 'Alex', text: 'We need to talk.'),
          PhoneCallLine(speaker: 'Boss', text: 'Not now.'),
        ],
        unlockTimestamp: t,
      );
      expect(call.lines.length, 2);
      expect(call.durationSeconds, 120);
      expect(call.contentType, 'phone_call');
    });
  });

  // ── GroupChatThread ──────────────────────────────────────
  group('GroupChatThread', () {
    test('GroupChatThread stores messages and members', () {
      final t = DateTime.now();
      final gc = GroupChatThread(
        platform: 'whatsapp',
        groupName: 'The Night Shift',
        members: ['Alex', 'Eve', 'Marcus'],
        messages: [
          GroupChatMessage(sender: 'Alex', text: 'Anyone up?'),
          GroupChatMessage(sender: 'Eve', text: 'Can\'t sleep.'),
        ],
        unlockTimestamp: t,
      );
      expect(gc.members.length, 3);
      expect(gc.messages.length, 2);
      expect(gc.contentType, 'group_chat');
    });
  });
}
