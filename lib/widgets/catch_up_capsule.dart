import 'package:flutter/material.dart';
import '../models/story_catchup_summary.dart';
import '../theme.dart';

/// Full-width catch-up capsule shown to returning users.
/// Summarizes missed content and provides quick actions.
class CatchUpCapsule extends StatelessWidget {
  final StoryCatchUpSummary summary;
  final VoidCallback? onReadRecap;
  final VoidCallback? onJumpIn;
  final VoidCallback? onSkip;

  const CatchUpCapsule({
    super.key,
    required this.summary,
    this.onReadRecap,
    this.onJumpIn,
    this.onSkip,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.surface,
            AppTheme.surfaceLow,
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.accentNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Eyebrow
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'WHILE YOU WERE AWAY',
                style: TextStyle(
                  color: AppTheme.accentNeon,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ),
              if (onSkip != null)
                GestureDetector(
                  onTap: onSkip,
                  child: Icon(
                    Icons.close,
                    color: AppTheme.textMuted,
                    size: 18,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          
          // Headline
          Text(
            summary.headline,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: AppTheme.textBody,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          
          // Missed count chips
          if (summary.missedCountsByType.isNotEmpty) ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: summary.missedCountsByType.entries.map((entry) {
                return _buildCountChip(entry.key, entry.value);
              }).toList(),
            ),
            const SizedBox(height: 16),
          ],
          
          // Bullets
          if (summary.bullets.isNotEmpty) ...[
            ...summary.bullets.take(3).map((bullet) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      margin: const EdgeInsets.only(top: 6, right: 10),
                      decoration: BoxDecoration(
                        color: AppTheme.accentNeon,
                        shape: BoxShape.circle,
                      ),
                    ),
                    Expanded(
                      child: Text(
                        bullet,
                        style: TextStyle(
                          color: AppTheme.textBody,
                          fontSize: 13,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 16),
          ],
          
          // Unresolved question
          if (summary.unresolvedQuestion.isNotEmpty) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.accentNeon.withOpacity(0.08),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: AppTheme.accentNeon.withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'UNRESOLVED',
                    style: TextStyle(
                      color: AppTheme.accentNeon,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    summary.unresolvedQuestion,
                    style: TextStyle(
                      color: AppTheme.accentNeon,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],
          
          // CTA Row
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: onReadRecap,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.textBody,
                    side: BorderSide(color: AppTheme.textMuted.withOpacity(0.3)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text('Read Recap'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton(
                  onPressed: onJumpIn,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentNeon,
                    foregroundColor: AppTheme.darkBg,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text(
                    'Jump In',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCountChip(String type, int count) {
    final displayName = StoryCatchUpSummary.getDisplayNameForType(type);
    final label = count == 1 ? displayName : '${displayName}s';
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppTheme.surfaceHigh,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
          color: AppTheme.textDim,
          fontSize: 11,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
