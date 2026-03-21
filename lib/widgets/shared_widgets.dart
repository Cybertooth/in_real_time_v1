import 'package:flutter/material.dart';
import '../theme.dart';

/// Shared UI building blocks used across multiple screens.

/// Small coloured pill — used for content type labels, platform badges, etc.
class TypeBadge extends StatelessWidget {
  final String label;
  final Color color;
  final IconData? icon;

  const TypeBadge({super.key, required this.label, required this.color, this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 10, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            label.toUpperCase(),
            style: TextStyle(
              color: color,
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}

/// Pulsing live indicator dot.
class LiveDot extends StatefulWidget {
  const LiveDot({super.key});

  @override
  State<LiveDot> createState() => _LiveDotState();
}

class _LiveDotState extends State<LiveDot> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 12,
          height: 12,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Ping ring
              AnimatedBuilder(
                animation: _ctrl,
                builder: (_, __) {
                  return Container(
                    width: 12 * (1 + _ctrl.value * 0.6),
                    height: 12 * (1 + _ctrl.value * 0.6),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppTheme.accentNeon.withOpacity(1 - _ctrl.value),
                        width: 1.5,
                      ),
                    ),
                  );
                },
              ),
              // Core dot
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: AppTheme.accentNeon,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: AppTheme.accentNeon.withOpacity(0.5), blurRadius: 6)],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 6),
        Text(
          'LIVE',
          style: TextStyle(
            color: AppTheme.accentNeon,
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 2,
          ),
        ),
      ],
    );
  }
}

/// Animated builder that rebuilds on every animation frame.
class AnimatedBuilder extends StatelessWidget {
  final Animation<double> animation;
  final Widget Function(BuildContext, Widget?) builder;

  const AnimatedBuilder({super.key, required this.animation, required this.builder});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder._internal(animation: animation, builder: builder);
  }

  // Use the built-in AnimatedBuilder under the hood
  static Widget _internal({
    required Animation<double> animation,
    required Widget Function(BuildContext, Widget?) builder,
  }) {
    return _AnimBuilderWidget(animation: animation, builder: builder);
  }
}

class _AnimBuilderWidget extends StatefulWidget {
  final Animation<double> animation;
  final Widget Function(BuildContext, Widget?) builder;

  const _AnimBuilderWidget({required this.animation, required this.builder});

  @override
  State<_AnimBuilderWidget> createState() => _AnimBuilderWidgetState();
}

class _AnimBuilderWidgetState extends State<_AnimBuilderWidget> {
  @override
  void initState() {
    super.initState();
    widget.animation.addListener(_onTick);
  }

  @override
  void dispose() {
    widget.animation.removeListener(_onTick);
    super.dispose();
  }

  void _onTick() => setState(() {});

  @override
  Widget build(BuildContext context) => widget.builder(context, null);
}

/// Formatted timestamp label.
class TimestampLabel extends StatelessWidget {
  final DateTime time;
  final bool showDate;

  const TimestampLabel({super.key, required this.time, this.showDate = true});

  @override
  Widget build(BuildContext context) {
    final h = time.hour.toString().padLeft(2, '0');
    final m = time.minute.toString().padLeft(2, '0');
    final dateStr = showDate
        ? '${time.year}-${time.month.toString().padLeft(2, '0')}-${time.day.toString().padLeft(2, '0')} '
        : '';
    return Text(
      '$dateStr$h:$m',
      style: Theme.of(context).textTheme.labelSmall,
    );
  }
}

/// A glowing "INTERCEPTED" label.
class InterceptedLabel extends StatelessWidget {
  const InterceptedLabel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        border: Border.all(color: AppTheme.accentNeon.withOpacity(0.3)),
        borderRadius: BorderRadius.circular(2),
        boxShadow: [BoxShadow(color: AppTheme.accentNeon.withOpacity(0.08), blurRadius: 8)],
      ),
      child: Text(
        'INTERCEPTED',
        style: TextStyle(
          color: AppTheme.accentNeon,
          fontSize: 8,
          fontWeight: FontWeight.w700,
          letterSpacing: 2,
        ),
      ),
    );
  }
}

/// Empty state placeholder.
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const EmptyState({super.key, required this.icon, required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppTheme.textMuted, size: 48),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: AppTheme.textDim)),
          const SizedBox(height: 8),
          Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
