import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

/// Full-screen list of intercepted voice memos.
class VoiceNoteScreen extends ConsumerWidget {
  const VoiceNoteScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notesAsync = ref.watch(voiceNoteProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('VOICE NOTES')),
      body: notesAsync.when(
        data: (notes) {
          if (notes.isEmpty) {
            return const EmptyState(
              icon: Icons.mic_off,
              title: 'NO RECORDINGS',
              subtitle: 'Intercepted voice recordings will appear here.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: notes.length,
            itemBuilder: (_, i) => _VoiceNoteDetailCard(note: notes[i], isFirst: i == 0),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _VoiceNoteDetailCard extends StatefulWidget {
  final VoiceNote note;
  final bool isFirst;
  const _VoiceNoteDetailCard({required this.note, this.isFirst = false});

  @override
  State<_VoiceNoteDetailCard> createState() => _VoiceNoteDetailCardState();
}

class _VoiceNoteDetailCardState extends State<_VoiceNoteDetailCard> {
  late final AudioPlayer _player;
  StreamSubscription<Duration>? _positionSub;
  StreamSubscription<Duration?>? _durationSub;
  StreamSubscription<PlayerState>? _stateSub;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _loadingAudio = false;
  bool _isPlaying = false;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _positionSub = _player.positionStream.listen((value) {
      if (mounted) setState(() => _position = value);
    });
    _durationSub = _player.durationStream.listen((value) {
      if (mounted) setState(() => _duration = value ?? Duration.zero);
    });
    _stateSub = _player.playerStateStream.listen((value) {
      if (mounted) {
        setState(() {
          _isPlaying = value.playing;
        });
      }
    });
  }

  @override
  void dispose() {
    _positionSub?.cancel();
    _durationSub?.cancel();
    _stateSub?.cancel();
    _player.dispose();
    super.dispose();
  }

  Future<void> _togglePlayback() async {
    final audioUrl = widget.note.audioUrl;
    if (audioUrl == null || audioUrl.isEmpty) return;

    if (_isPlaying) {
      await _player.pause();
      return;
    }

    if (_player.audioSource == null) {
      setState(() => _loadingAudio = true);
      try {
        await _player.setUrl(audioUrl);
      } finally {
        if (mounted) setState(() => _loadingAudio = false);
      }
    }

    await _player.play();
  }

  String _format(Duration d) {
    final mm = d.inMinutes.toString().padLeft(2, '0');
    final ss = (d.inSeconds % 60).toString().padLeft(2, '0');
    return '$mm:$ss';
  }

  @override
  Widget build(BuildContext context) {
    final note = widget.note;
    final hasAudio = (note.audioUrl ?? '').isNotEmpty;
    final progressMax = _duration.inMilliseconds > 0 ? _duration.inMilliseconds.toDouble() : 1.0;
    final progressValue = _position.inMilliseconds.clamp(0, progressMax.toInt()).toDouble();

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(
        accentBorder: AppTheme.voiceNoteColor,
        glow: widget.isFirst,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppTheme.voiceNoteColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.mic, size: 16, color: AppTheme.voiceNoteColor),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(note.speaker, style: const TextStyle(color: AppTheme.voiceNoteColor, fontWeight: FontWeight.w600, fontSize: 14)),
                    TimestampLabel(time: note.unlockTimestamp),
                  ],
                ),
              ),
              if (widget.isFirst) const InterceptedLabel(),
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: hasAudio ? AppTheme.voiceNoteColor.withOpacity(0.12) : Colors.white10,
                  shape: BoxShape.circle,
                  border: Border.all(color: hasAudio ? AppTheme.voiceNoteColor.withOpacity(0.35) : Colors.white24),
                ),
                child: IconButton(
                  onPressed: hasAudio && !_loadingAudio ? _togglePlayback : null,
                  iconSize: 16,
                  color: hasAudio ? AppTheme.voiceNoteColor : Colors.white30,
                  icon: _loadingAudio
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.voiceNoteColor),
                        )
                      : Icon(_isPlaying ? Icons.pause : Icons.play_arrow),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 5),
              activeTrackColor: AppTheme.voiceNoteColor,
              thumbColor: AppTheme.voiceNoteColor,
              inactiveTrackColor: Colors.white24,
            ),
            child: Slider(
              value: progressValue,
              min: 0,
              max: progressMax,
              onChanged: hasAudio && _duration > Duration.zero
                  ? (value) => _player.seek(Duration(milliseconds: value.toInt()))
                  : null,
            ),
          ),
          Row(
            children: [
              Text(_format(_position), style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
              const Spacer(),
              Text(
                hasAudio ? _format(_duration) : 'Audio unavailable',
                style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            note.transcript,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic, height: 1.6),
          ),
        ],
      ),
    );
  }
}
