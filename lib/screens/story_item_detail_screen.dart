import 'package:flutter/material.dart';
import '../models/story_item.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

class StoryItemDetailScreen extends StatelessWidget {
  final StoryItem item;

  const StoryItemDetailScreen({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(item.contentType.toUpperCase()),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: _buildContent(context),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    return switch (item) {
      Journal j => _JournalDetail(item: j),
      Email e => _EmailDetail(item: e),
      Receipt r => _ReceiptDetail(item: r),
      VoiceNote v => _VoiceNoteDetail(item: v),
      SocialPost s => _SocialPostDetail(item: s),
      PhoneCall p => _PhoneCallDetail(item: p),
      _ => Text('Unsupported content type: ${item.contentType}'),
    };
  }
}

class _JournalDetail extends StatelessWidget {
  final Journal item;
  const _JournalDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TimestampLabel(time: item.unlockTimestamp),
        const SizedBox(height: 16),
        Text(
          item.title,
          style: Theme.of(context).textTheme.displayLarge?.copyWith(
                color: AppTheme.journalColor,
                fontSize: 24,
              ),
        ),
        const SizedBox(height: 24),
        Text(
          item.body,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                height: 1.8,
                letterSpacing: 0.2,
              ),
        ),
      ],
    );
  }
}

class _EmailDetail extends StatelessWidget {
  final Email item;
  const _EmailDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            CircleAvatar(
              backgroundColor: AppTheme.emailColor.withOpacity(0.1),
              child: const Icon(Icons.email, color: AppTheme.emailColor),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.sender, style: const TextStyle(fontWeight: FontWeight.bold)),
                  TimestampLabel(time: item.unlockTimestamp),
                ],
              ),
            ),
          ],
        ),
        const Divider(height: 48),
        Text(
          item.subject,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: Colors.white,
              ),
        ),
        const SizedBox(height: 24),
        Text(
          item.body,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6),
        ),
      ],
    );
  }
}

class _ReceiptDetail extends StatelessWidget {
  final Receipt item;
  const _ReceiptDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: AppTheme.cardDecoration(accentBorder: AppTheme.receiptColor),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.receipt_long, color: AppTheme.receiptColor, size: 48),
            const SizedBox(height: 16),
            Text(item.merchantName.toUpperCase(),
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2)),
            const SizedBox(height: 8),
            TimestampLabel(time: item.unlockTimestamp),
            const Divider(height: 40),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(item.description, style: AppTheme.darkTheme.textTheme.bodyMedium),
                Text('\$${item.amount.toStringAsFixed(2)}',
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.accentNeon)),
              ],
            ),
            const SizedBox(height: 40),
            const Text('TRANSACTION_VERIFIED',
                style: TextStyle(color: AppTheme.textMuted, fontSize: 10, letterSpacing: 4)),
          ],
        ),
      ),
    );
  }
}

class _VoiceNoteDetail extends StatelessWidget {
  final VoiceNote item;
  const _VoiceNoteDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 40),
        const Icon(Icons.mic, color: AppTheme.voiceNoteColor, size: 64),
        const SizedBox(height: 24),
        Text(item.speaker, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TimestampLabel(time: item.unlockTimestamp),
        const SizedBox(height: 48),
        Container(
          padding: const EdgeInsets.all(20),
          decoration: AppTheme.glassDecoration(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('TRANSCRIPT',
                  style: TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 2)),
              const SizedBox(height: 12),
              Text(item.transcript, style: const TextStyle(fontStyle: FontStyle.italic, height: 1.5)),
            ],
          ),
        ),
      ],
    );
  }
}

class _SocialPostDetail extends StatelessWidget {
  final SocialPost item;
  const _SocialPostDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            CircleAvatar(
              backgroundColor: AppTheme.socialPostColor.withOpacity(0.1),
              child: Text(item.author[0]),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.author, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text('@${item.handle}', style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
              ],
            ),
            const Spacer(),
            Text(item.platform.toUpperCase(),
                style: TextStyle(color: AppTheme.socialPostColor, fontSize: 10, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 24),
        Text(item.content, style: const TextStyle(fontSize: 18, height: 1.4)),
        const SizedBox(height: 24),
        const Divider(),
        const SizedBox(height: 12),
        Row(
          children: [
            const Icon(Icons.favorite, color: AppTheme.alertRed, size: 20),
            const SizedBox(width: 6),
            Text('${item.likes}'),
            const SizedBox(width: 24),
            const Icon(Icons.chat_bubble_outline, color: AppTheme.textDim, size: 20),
            const SizedBox(width: 6),
            Text('${item.comments}'),
          ],
        ),
      ],
    );
  }
}

class _PhoneCallDetail extends StatelessWidget {
  final PhoneCall item;
  const _PhoneCallDetail({required this.item});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('CALL LOG', style: TextStyle(color: AppTheme.phoneCallColor, fontSize: 10, fontWeight: FontWeight.bold)),
                Text('${item.caller} ↔ ${item.receiver}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            TimestampLabel(time: item.unlockTimestamp),
          ],
        ),
        const SizedBox(height: 32),
        const Text('INTERCEPTED AUDIO TRANSCRIPT',
            style: TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        const SizedBox(height: 16),
        ...item.lines.map((line) => Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(line.speaker.toUpperCase(),
                      style: TextStyle(
                          color: line.speaker == item.caller ? AppTheme.accentNeon : AppTheme.tertiary,
                          fontSize: 11,
                          fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(line.text, style: const TextStyle(height: 1.4)),
                ],
              ),
            )),
      ],
    );
  }
}
