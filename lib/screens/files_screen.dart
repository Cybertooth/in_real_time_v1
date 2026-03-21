import 'package:flutter/material.dart';
import 'wallet_screen.dart';
import 'voice_note_screen.dart';
import 'social_post_screen.dart';
import 'phone_call_screen.dart';
import 'group_chat_screen.dart';
import '../theme.dart';

/// The "Files" tab — a hub that links to receipts, voice notes, social posts,
/// phone calls, and group chats.
class FilesScreen extends StatelessWidget {
  const FilesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FILES')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _FileTile(
            icon: Icons.receipt_long,
            label: 'RECEIPTS & TRANSACTIONS',
            color: AppTheme.receiptColor,
            onTap: () => _push(context, const WalletScreen()),
          ),
          const SizedBox(height: 10),
          _FileTile(
            icon: Icons.mic,
            label: 'VOICE NOTES',
            color: AppTheme.voiceNoteColor,
            onTap: () => _push(context, const VoiceNoteScreen()),
          ),
          const SizedBox(height: 10),
          _FileTile(
            icon: Icons.public,
            label: 'SOCIAL INTERCEPTS',
            color: AppTheme.socialPostColor,
            onTap: () => _push(context, const SocialPostScreen()),
          ),
          const SizedBox(height: 10),
          _FileTile(
            icon: Icons.phone,
            label: 'PHONE CALLS',
            color: AppTheme.phoneCallColor,
            onTap: () => _push(context, const PhoneCallScreen()),
          ),
          const SizedBox(height: 10),
          _FileTile(
            icon: Icons.group,
            label: 'GROUP CHATS',
            color: AppTheme.groupChatColor,
            onTap: () => _push(context, const GroupChatScreen()),
          ),
        ],
      ),
    );
  }

  void _push(BuildContext context, Widget screen) {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => screen,
        transitionsBuilder: (_, anim, __, child) {
          return FadeTransition(
            opacity: anim,
            child: ScaleTransition(
              scale: Tween<double>(begin: 0.96, end: 1.0).animate(
                CurvedAnimation(parent: anim, curve: Curves.easeOut),
              ),
              child: child,
            ),
          );
        },
        transitionDuration: const Duration(milliseconds: 250),
      ),
    );
  }
}

class _FileTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _FileTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: AppTheme.cardDecoration(accentBorder: color),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w600,
                  fontSize: 13,
                  letterSpacing: 1.0,
                ),
              ),
            ),
            const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
          ],
        ),
      ),
    );
  }
}
