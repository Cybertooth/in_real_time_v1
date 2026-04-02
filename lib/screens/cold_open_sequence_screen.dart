import 'dart:async';
import 'package:flutter/material.dart';
import '../models/cold_open_step.dart';
import '../theme.dart';
import 'cold_open_decision_screen.dart';

class ColdOpenSequenceScreen extends StatefulWidget {
  final VoidCallback onSkip;
  final VoidCallback onComplete;

  const ColdOpenSequenceScreen({
    super.key,
    required this.onSkip,
    required this.onComplete,
  });

  @override
  State<ColdOpenSequenceScreen> createState() => _ColdOpenSequenceScreenState();
}

class _ColdOpenSequenceScreenState extends State<ColdOpenSequenceScreen>
    with TickerProviderStateMixin {
  int _currentStep = 0;
  Timer? _timer;
  late AnimationController _stepFadeController;

  @override
  void initState() {
    super.initState();
    _stepFadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _startStep();
  }

  void _startStep() {
    _stepFadeController.forward(from: 0);
    final step = defaultColdOpenScript[_currentStep];
    _timer = Timer(step.displayDuration, _advanceStep);
  }

  void _advanceStep() {
    if (_currentStep >= defaultColdOpenScript.length - 1) {
      _goToDecision();
      return;
    }
    _stepFadeController.reverse().then((_) {
      if (!mounted) return;
      setState(() => _currentStep++);
      _startStep();
    });
  }

  void _goToDecision() {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => ColdOpenDecisionScreen(
          onComplete: widget.onComplete,
          onSkip: widget.onSkip,
        ),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
        transitionDuration: const Duration(milliseconds: 600),
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _stepFadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final step = defaultColdOpenScript[_currentStep];
    final progress = (_currentStep + 1) / defaultColdOpenScript.length;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Progress bar
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            left: 20,
            right: 20,
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.white10,
              color: AppTheme.accentNeon.withOpacity(0.6),
              minHeight: 2,
            ),
          ),
          // Content
          Center(
            child: FadeTransition(
              opacity: _stepFadeController,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 28),
                child: _buildStepContent(step),
              ),
            ),
          ),
          // Skip button
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            right: 20,
            child: GestureDetector(
              onTap: widget.onSkip,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white24),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: const Text(
                  'Skip',
                  style: TextStyle(
                    color: Colors.white38,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepContent(ColdOpenStep step) {
    switch (step.type) {
      case ColdOpenStepType.text:
        return _buildTextStep(step);
      case ColdOpenStepType.chat:
        return _buildChatStep(step);
      case ColdOpenStepType.receipt:
        return _buildReceiptStep(step);
      case ColdOpenStepType.image:
        return _buildTextStep(step);
      case ColdOpenStepType.journal:
        return _buildJournalStep(step);
      case ColdOpenStepType.cliffhanger:
        return _buildCliffhangerStep(step);
    }
  }

  Widget _buildTextStep(ColdOpenStep step) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (step.title != null) ...[
          Text(
            step.title!,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppTheme.accentNeon.withOpacity(0.5),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 3,
            ),
          ),
          const SizedBox(height: 12),
        ],
        Text(
          step.body ?? '',
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 15,
            height: 1.6,
          ),
        ),
      ],
    );
  }

  Widget _buildChatStep(ColdOpenStep step) {
    final isProta = step.isProtagonist;
    return Align(
      alignment: isProta ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isProta
              ? AppTheme.accentNeon.withOpacity(0.12)
              : Colors.white.withOpacity(0.06),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isProta ? 16 : 4),
            bottomRight: Radius.circular(isProta ? 4 : 16),
          ),
          border: Border.all(
            color: isProta
                ? AppTheme.accentNeon.withOpacity(0.2)
                : Colors.white12,
          ),
        ),
        child: Column(
          crossAxisAlignment:
              isProta ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              step.sender ?? '',
              style: TextStyle(
                color: isProta ? AppTheme.accentNeon : Colors.white38,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              step.body ?? '',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReceiptStep(ColdOpenStep step) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            step.title ?? 'RECEIPT',
            style: TextStyle(
              color: AppTheme.accentNeon.withOpacity(0.6),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            step.body ?? '',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontFamily: 'monospace',
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildJournalStep(ColdOpenStep step) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.accentNeon.withOpacity(0.04),
        borderRadius: BorderRadius.circular(4),
        border: Border(
          left: BorderSide(color: AppTheme.accentNeon.withOpacity(0.3), width: 3),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            step.title ?? 'Journal',
            style: TextStyle(
              color: AppTheme.accentNeon.withOpacity(0.6),
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            step.body ?? '',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontStyle: FontStyle.italic,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCliffhangerStep(ColdOpenStep step) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Pulsing signal
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: AppTheme.alertRed,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: AppTheme.alertRed.withOpacity(0.5),
                blurRadius: 16,
                spreadRadius: 2,
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        Text(
          step.title ?? 'SIGNAL LOST',
          style: TextStyle(
            color: AppTheme.alertRed.withOpacity(0.7),
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 4,
          ),
        ),
        const SizedBox(height: 16),
        Text(
          step.body ?? '',
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white60,
            fontSize: 16,
            fontStyle: FontStyle.italic,
            height: 1.5,
          ),
        ),
      ],
    );
  }
}
