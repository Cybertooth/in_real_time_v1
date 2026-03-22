import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

class ChatThreadScreen extends ConsumerWidget {
  final String conversationId;
  final String title;
  final bool isGroup;

  const ChatThreadScreen({
    super.key,
    required this.conversationId,
    required this.title,
    this.isGroup = false,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (isGroup) {
      final groups = ref.watch(groupChatProvider).value ?? [];
      final group = groups.firstWhere((g) => g.id == conversationId);
      return _buildThread(context, group.messages.map((m) => _MessageData(
        sender: m.sender,
        text: m.text,
        isProtagonist: false, // In group chats, we treat others as external for simplicity
        timestamp: group.unlockTimestamp,
        imageUrl: m == group.messages.last ? group.imageUrl : null,
      )).toList());
    } else {
      final chats = ref.watch(chatProvider).value ?? [];
      final threadMessages = chats.where((c) => c.senderId == conversationId).toList();
      return _buildThread(context, threadMessages.map((c) => _MessageData(
        sender: c.senderId,
        text: c.text,
        isProtagonist: c.isProtagonist,
        timestamp: c.unlockTimestamp,
        imageUrl: c.imageUrl,
      )).toList());
    }
  }

  Widget _buildThread(BuildContext context, List<_MessageData> messages) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 16)),
            Text(isGroup ? 'Encrypted Group' : 'Direct Message', 
                 style: const TextStyle(fontSize: 10, color: AppTheme.textMuted, letterSpacing: 1)),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                return _TypingAwareBubble(data: msg);
              },
            ),
          ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      decoration: BoxDecoration(
        color: AppTheme.surfaceLow,
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.04))),
      ),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.08)),
        ),
        child: Row(
          children: [
            const Expanded(
              child: TextField(
                enabled: false,
                decoration: InputDecoration(
                  hintText: 'SYSTEM_READ_ONLY',
                  hintStyle: TextStyle(color: AppTheme.textMuted, fontSize: 13, letterSpacing: 1),
                  border: InputBorder.none,
                ),
              ),
            ),
            Icon(Icons.lock_outline, size: 18, color: AppTheme.textMuted.withOpacity(0.5)),
          ],
        ),
      ),
    );
  }
}

class _MessageData {
  final String sender;
  final String text;
  final bool isProtagonist;
  final DateTime timestamp;
  final String? imageUrl;

  _MessageData({
    required this.sender,
    required this.text,
    required this.isProtagonist,
    required this.timestamp,
    this.imageUrl,
  });
}

class _TypingAwareBubble extends StatefulWidget {
  final _MessageData data;
  const _TypingAwareBubble({required this.data});

  @override
  State<_TypingAwareBubble> createState() => _TypingAwareBubbleState();
}

class _TypingAwareBubbleState extends State<_TypingAwareBubble> {
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    _checkTyping();
  }

  @override
  void didUpdateWidget(covariant _TypingAwareBubble oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.data.timestamp != widget.data.timestamp) {
      _checkTyping();
    }
  }

  void _checkTyping() {
    if (widget.data.isProtagonist) {
      _isTyping = false;
      return;
    }
    
    final diff = DateTime.now().difference(widget.data.timestamp);
    if (diff.inSeconds < 3 && diff.inSeconds >= 0) {
      setState(() => _isTyping = true);
      Future.delayed(Duration(seconds: 3 - diff.inSeconds), () {
        if (mounted) setState(() => _isTyping = false);
      });
    } else {
      _isTyping = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isTyping) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 4),
              child: Text(widget.data.sender, style: const TextStyle(color: AppTheme.chatColor, fontSize: 11, fontWeight: FontWeight.bold)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.05)),
              ),
              child: const Text('...', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.accentNeon, letterSpacing: 2)),
            ),
          ],
        ),
      );
    }
    return _ChatBubble(data: widget.data);
  }
}

class _ChatBubble extends StatelessWidget {
  final _MessageData data;
  const _ChatBubble({required this.data});

  @override
  Widget build(BuildContext context) {
    final isMe = data.isProtagonist;
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (!isMe)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 4),
              child: Text(data.sender, style: const TextStyle(color: AppTheme.chatColor, fontSize: 11, fontWeight: FontWeight.bold)),
            ),
          Container(
            padding: const EdgeInsets.all(12),
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
            decoration: BoxDecoration(
              color: isMe ? AppTheme.accentNeon.withOpacity(0.1) : AppTheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: isMe ? AppTheme.accentNeon.withOpacity(0.2) : Colors.white.withOpacity(0.05)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (data.imageUrl != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.network(
                        data.imageUrl!,
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                Text(data.text, style: const TextStyle(fontSize: 14, height: 1.4)),
              ],
            ),
          ),
          const SizedBox(height: 4),
          TimestampLabel(time: data.timestamp, showDate: false),
        ],
      ),
    );
  }
}
