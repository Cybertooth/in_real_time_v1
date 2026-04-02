import 'package:flutter/material.dart';
import '../theme.dart';

/// Banner shown during binge mode showing progress toward the live wall.
class BingeProgressBanner extends StatelessWidget {
  final int currentCount;
  final int totalCount;
  final VoidCallback? onDismiss;

  const BingeProgressBanner({
    super.key,
    required this.currentCount,
    required this.totalCount,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final progress = (currentCount / totalCount).clamp(0.0, 1.0);
    
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.fast_forward,
                color: AppTheme.accentNeon,
                size: 18,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'CATCHING UP TO LIVE',
                  style: TextStyle(
                    color: AppTheme.accentNeon,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.2,
                  ),
                ),
              ),
              if (onDismiss != null)
                GestureDetector(
                  onTap: onDismiss,
                  child: Icon(
                    Icons.close,
                    color: AppTheme.textMuted,
                    size: 16,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: AppTheme.accentNeon.withOpacity(0.1),
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accentNeon),
              minHeight: 4,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '$currentCount of $totalCount opening intercepts',
            style: TextStyle(
              color: AppTheme.textMuted,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}
