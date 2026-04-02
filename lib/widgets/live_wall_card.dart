import 'package:flutter/material.dart';
import '../theme.dart';

/// Card shown when user reaches the binge boundary, transitioning to live mode.
class LiveWallCard extends StatelessWidget {
  final DateTime? nextUnlockAt;
  final VoidCallback? onEnableReminders;
  final VoidCallback? onContinue;

  const LiveWallCard({
    super.key,
    this.nextUnlockAt,
    this.onEnableReminders,
    this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    final nextUnlockText = nextUnlockAt != null
        ? _formatTimeUntil(nextUnlockAt!)
        : 'Stay tuned for the next update';

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.surface,
            AppTheme.surface.withOpacity(0.8),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.accentNeon.withOpacity(0.5),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.accentNeon.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.check_circle,
              color: AppTheme.accentNeon,
              size: 28,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            "YOU'RE NOW CAUGHT UP",
            style: TextStyle(
              color: AppTheme.accentNeon,
              fontSize: 14,
              fontWeight: FontWeight.bold,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            "You've reached the live wall. New content will unlock according to the real-time schedule.",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppTheme.textBody,
              fontSize: 13,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: AppTheme.accentNeon.withOpacity(0.08),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.schedule,
                  color: AppTheme.accentNeon,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Text(
                  'Next unlock: $nextUnlockText',
                  style: TextStyle(
                    color: AppTheme.accentNeon,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (onEnableReminders != null)
            TextButton.icon(
              onPressed: onEnableReminders,
              icon: const Icon(Icons.notifications_active, size: 16),
              label: const Text('Enable reminders'),
              style: TextButton.styleFrom(
                foregroundColor: AppTheme.textMuted,
              ),
            ),
          if (onContinue != null)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.accentNeon,
                  foregroundColor: AppTheme.darkBg,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: const Text(
                  'CONTINUE',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  String _formatTimeUntil(DateTime target) {
    final now = DateTime.now();
    final diff = target.difference(now);

    if (diff.isNegative) return 'Any moment now';
    
    if (diff.inDays > 0) {
      return '${diff.inDays}d ${diff.inHours % 24}h';
    } else if (diff.inHours > 0) {
      return '${diff.inHours}h ${diff.inMinutes % 60}m';
    } else if (diff.inMinutes > 0) {
      return '${diff.inMinutes}m';
    } else {
      return 'Any moment now';
    }
  }
}
