import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';
import 'story_item_detail_screen.dart';
import 'chat_thread_screen.dart';

/// The home screen — a unified chronological feed of all intercepted content.
class TimelineScreen extends ConsumerWidget {
  const TimelineScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedAsync = ref.watch(timelineFeedProvider);
    final hasUpcoming = ref.watch(upcomingItemsProvider).value ?? false;
    final unlockedLocally = ref.watch(unlockedItemsProvider).value ?? {};
    final activeStory = ref.watch(activeStoryProvider).valueOrNull;
    final burstStatusAsync = ref.watch(onDemandBurstStatusProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('IN REAL TIME'),
        actions: const [
          Padding(padding: EdgeInsets.only(right: 16), child: LiveDot()),
        ],
      ),
      body: feedAsync.when(
        data: (items) {
          if (items.isEmpty && !hasUpcoming) {
            return const EmptyState(
              icon: Icons.signal_wifi_statusbar_null,
              title: 'AWAITING SIGNAL',
              subtitle: 'No intercepted data yet. Stand by...',
            );
          }
          final burstBanner = activeStory?.isOnDemandSubscription == true
              ? burstStatusAsync.maybeWhen(
                  data: (status) {
                    if (status == null) return const SizedBox.shrink();
                    final nextText = status.nextUnlockAt == null
                        ? 'This burst is complete.'
                        : 'Next drop in ${status.nextUnlockAt!.difference(DateTime.now()).inSeconds.clamp(0, 9999)}s';
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.accentNeon.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: AppTheme.accentNeon.withOpacity(0.35),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.bolt,
                            color: AppTheme.accentNeon,
                            size: 18,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Burst Mode: ${status.unlockedInBurst} unlocked, ${status.pendingInBurst} pending. $nextText',
                              style: const TextStyle(
                                color: AppTheme.accentNeon,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                  orElse: SizedBox.shrink,
                )
              : const SizedBox.shrink();
          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            itemCount: items.length + (hasUpcoming ? 1 : 0) + 1,
            itemBuilder: (context, index) {
              if (index == 0) {
                return burstBanner;
              }
              final adjusted = index - 1;
              if (adjusted == 0 && hasUpcoming) {
                return _LockedCard();
              }
              final item = items[hasUpcoming ? adjusted - 1 : adjusted];
              final isUnlockedLocally = unlockedLocally.contains(item.id);
              final isLocked = item.isPasswordLocked && !isUnlockedLocally;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _buildCard(context, ref, item, isLocked),
              );
            },
          );
        },
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.accentNeon),
        ),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Widget _buildCard(
    BuildContext context,
    WidgetRef ref,
    StoryItem item,
    bool isLocked,
  ) {
    final card = switch (item) {
      Journal j => _JournalCard(item: j),
      Chat c => _ChatCard(item: c),
      Email e => _EmailCard(item: e),
      Receipt r => _ReceiptCard(item: r),
      VoiceNote v => _VoiceNoteCard(item: v),
      SocialPost s => _SocialPostCard(item: s),
      PhoneCall p => _PhoneCallCard(item: p),
      GroupChatThread g => _GroupChatCard(item: g),
      _ => const SizedBox.shrink(),
    };

    Widget displayCard = card;
    if (isLocked) {
      displayCard = Stack(
        children: [
          Opacity(opacity: 0.5, child: IgnorePointer(child: card)),
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.4),
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Center(
                child: Icon(Icons.lock, color: AppTheme.accentNeon, size: 36),
              ),
            ),
          ),
        ],
      );
    }

    return InkWell(
      onTap: () async {
        if (isLocked) {
          final success = await _promptPassword(context, item);
          if (success != true) return;
          // Trigger a refresh of the unlocked items provider
          ref.invalidate(unlockedItemsProvider);
        }

        if (!context.mounted) return;

        if (item is Chat) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ChatThreadScreen(
                conversationId: item.senderId,
                title: item.senderId,
                isGroup: false,
              ),
            ),
          );
        } else if (item is GroupChatThread) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ChatThreadScreen(
                conversationId: item.id,
                title: item.groupName,
                isGroup: true,
              ),
            ),
          );
        } else {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => StoryItemDetailScreen(item: item),
            ),
          );
        }
      },
      child: displayCard,
    );
  }

  Future<bool> _promptPassword(BuildContext context, StoryItem item) async {
    final controller = TextEditingController();
    bool error = false;

    return await showDialog<bool>(
          context: context,
          barrierDismissible: true,
          builder: (ctx) {
            return StatefulBuilder(
              builder: (ctx, setState) {
                return AlertDialog(
                  backgroundColor: AppTheme.surfaceLow,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: const BorderSide(color: AppTheme.accentNeon),
                  ),
                  title: const Row(
                    children: [
                      Icon(Icons.lock, color: AppTheme.accentNeon),
                      SizedBox(width: 8),
                      Text(
                        'ENCRYPTED',
                        style: TextStyle(
                          color: AppTheme.accentNeon,
                          letterSpacing: 2,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('Enter password or PIN to decrypt this file.'),
                      const SizedBox(height: 16),
                      TextField(
                        controller: controller,
                        obscureText: true,
                        autofocus: true,
                        style: const TextStyle(
                          color: Colors.white,
                          fontFamily: 'monospace',
                          letterSpacing: 8,
                          fontSize: 24,
                        ),
                        textAlign: TextAlign.center,
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: AppTheme.surface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(
                              color: AppTheme.accentNeon,
                            ),
                          ),
                          errorText: error ? 'INCORRECT PASSWORD' : null,
                        ),
                      ),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text(
                        'CANCEL',
                        style: TextStyle(color: AppTheme.textMuted),
                      ),
                    ),
                    TextButton(
                      onPressed: () async {
                        if (controller.text.trim() == item.unlockPassword) {
                          final prefs = await SharedPreferences.getInstance();
                          await prefs.setBool('unlocked_${item.id}', true);
                          if (ctx.mounted) Navigator.pop(ctx, true);
                        } else {
                          setState(() => error = true);
                        }
                      },
                      child: const Text(
                        'DECRYPT',
                        style: TextStyle(
                          color: AppTheme.accentNeon,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                );
              },
            );
          },
        ) ??
        false;
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Locked / Encrypted card
// ────────────────────────────────────────────────────────────────────────────
class _LockedCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.glassDecoration(),
      child: Column(
        children: [
          Icon(Icons.lock_outline, color: AppTheme.textMuted, size: 28),
          const SizedBox(height: 10),
          Text(
            'ENCRYPTED_FILE_LOCKED',
            style: TextStyle(
              color: AppTheme.textMuted,
              fontFamily: 'monospace',
              fontSize: 12,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Waiting for next synchronization event…',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Journal card
// ────────────────────────────────────────────────────────────────────────────
class _JournalCard extends StatelessWidget {
  final Journal item;
  const _JournalCard({required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(accentBorder: AppTheme.journalColor),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const TypeBadge(
                label: 'Journal',
                color: AppTheme.journalColor,
                icon: Icons.auto_stories,
              ),
              const Spacer(),
              TimestampLabel(time: item.unlockTimestamp),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            item.title.toUpperCase(),
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: AppTheme.accentNeon,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            item.body,
            maxLines: 4,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Chat card
// ────────────────────────────────────────────────────────────────────────────
class _ChatCard extends StatelessWidget {
  final Chat item;
  const _ChatCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final isMe = item.isProtagonist;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isMe ? AppTheme.accentNeon.withOpacity(0.06) : AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: isMe
              ? AppTheme.accentNeon.withOpacity(0.15)
              : Colors.white.withOpacity(0.04),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.chat_bubble,
            size: 16,
            color: AppTheme.chatColor.withOpacity(0.6),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      item.senderId,
                      style: TextStyle(
                        color: AppTheme.chatColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                    const Spacer(),
                    TimestampLabel(time: item.unlockTimestamp, showDate: false),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  item.text,
                  style: Theme.of(context).textTheme.bodyMedium,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Email card
// ────────────────────────────────────────────────────────────────────────────
class _EmailCard extends StatelessWidget {
  final Email item;
  const _EmailCard({required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(accentBorder: AppTheme.emailColor),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const TypeBadge(
                label: 'Email',
                color: AppTheme.emailColor,
                icon: Icons.email,
              ),
              const Spacer(),
              TimestampLabel(time: item.unlockTimestamp, showDate: false),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            item.sender,
            style: TextStyle(
              color: AppTheme.emailColor,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            item.subject,
            style: Theme.of(context).textTheme.headlineSmall,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            item.body,
            style: Theme.of(context).textTheme.bodySmall,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Receipt card
// ────────────────────────────────────────────────────────────────────────────
class _ReceiptCard extends StatelessWidget {
  final Receipt item;
  const _ReceiptCard({required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(accentBorder: AppTheme.receiptColor),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const TypeBadge(
                      label: 'Transaction',
                      color: AppTheme.receiptColor,
                      icon: Icons.receipt_long,
                    ),
                    const Spacer(),
                    TimestampLabel(time: item.unlockTimestamp, showDate: false),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  item.merchantName.toUpperCase(),
                  style: const TextStyle(
                    color: AppTheme.textBody,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  item.description,
                  style: Theme.of(context).textTheme.bodySmall,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '\$${item.amount.toStringAsFixed(2)}',
            style: const TextStyle(
              color: AppTheme.accentNeon,
              fontWeight: FontWeight.bold,
              fontSize: 20,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Voice Note card
// ────────────────────────────────────────────────────────────────────────────
class _VoiceNoteCard extends StatelessWidget {
  final VoiceNote item;
  const _VoiceNoteCard({required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.voiceNoteColor,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const TypeBadge(
                label: 'Voice Note',
                color: AppTheme.voiceNoteColor,
                icon: Icons.mic,
              ),
              const Spacer(),
              TimestampLabel(time: item.unlockTimestamp, showDate: false),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            item.speaker,
            style: TextStyle(
              color: AppTheme.voiceNoteColor,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 8),
          // Decorative waveform bars
          SizedBox(
            height: 24,
            child: Row(
              children: List.generate(30, (i) {
                final h = 6.0 + (i * 7 % 18);
                return Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 1),
                    height: h,
                    decoration: BoxDecoration(
                      color: AppTheme.voiceNoteColor.withOpacity(
                        0.4 + (i % 3) * 0.15,
                      ),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            item.transcript,
            style: Theme.of(context).textTheme.bodySmall,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Social Post card
// ────────────────────────────────────────────────────────────────────────────
class _SocialPostCard extends StatelessWidget {
  final SocialPost item;
  const _SocialPostCard({required this.item});

  IconData _platformIcon(String p) => switch (p.toLowerCase()) {
    'instagram' => Icons.camera_alt,
    'twitter' => Icons.alternate_email,
    'facebook' => Icons.facebook,
    'tiktok' => Icons.music_note,
    _ => Icons.public,
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.socialPostColor,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              TypeBadge(
                label: item.platform,
                color: AppTheme.socialPostColor,
                icon: _platformIcon(item.platform),
              ),
              const Spacer(),
              TimestampLabel(time: item.unlockTimestamp, showDate: false),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              CircleAvatar(
                radius: 14,
                backgroundColor: AppTheme.socialPostColor.withOpacity(0.15),
                child: Text(
                  item.author.isNotEmpty ? item.author[0].toUpperCase() : '?',
                  style: TextStyle(
                    color: AppTheme.socialPostColor,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.author,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                  Text(
                    '@${item.handle}',
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            item.content,
            style: Theme.of(context).textTheme.bodyMedium,
            maxLines: 4,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.favorite_border, size: 14, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text(
                '${item.likes}',
                style: Theme.of(context).textTheme.labelSmall,
              ),
              const SizedBox(width: 16),
              Icon(
                Icons.chat_bubble_outline,
                size: 14,
                color: AppTheme.textMuted,
              ),
              const SizedBox(width: 4),
              Text(
                '${item.comments}',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Phone Call card
// ────────────────────────────────────────────────────────────────────────────
class _PhoneCallCard extends StatelessWidget {
  final PhoneCall item;
  const _PhoneCallCard({required this.item});

  String _formatDuration(int secs) {
    final m = secs ~/ 60;
    final s = secs % 60;
    return '${m}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.phoneCallColor,
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppTheme.phoneCallColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Icon(
              Icons.phone,
              color: AppTheme.phoneCallColor,
              size: 18,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const TypeBadge(
                      label: 'Call',
                      color: AppTheme.phoneCallColor,
                      icon: Icons.phone,
                    ),
                    const Spacer(),
                    TimestampLabel(time: item.unlockTimestamp, showDate: false),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  '${item.caller}  →  ${item.receiver}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Duration: ${_formatDuration(item.durationSeconds)}  •  ${item.lines.length} lines',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
        ],
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Group Chat card
// ────────────────────────────────────────────────────────────────────────────
class _GroupChatCard extends StatelessWidget {
  final GroupChatThread item;
  const _GroupChatCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final lastMsg = item.messages.isNotEmpty ? item.messages.last : null;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.groupChatColor,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              TypeBadge(
                label: item.platform,
                color: AppTheme.groupChatColor,
                icon: Icons.group,
              ),
              const Spacer(),
              TimestampLabel(time: item.unlockTimestamp, showDate: false),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            item.groupName,
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 2),
          Text(
            '${item.members.length} members  •  ${item.messages.length} messages',
            style: Theme.of(context).textTheme.labelSmall,
          ),
          if (lastMsg != null) ...[
            const SizedBox(height: 8),
            Text(
              '${lastMsg.sender}: ${lastMsg.text}',
              style: Theme.of(context).textTheme.bodySmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }
}
