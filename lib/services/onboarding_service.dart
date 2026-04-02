import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kHasSeenColdOpen = 'has_seen_cold_open';
const _kColdOpenCompletedAt = 'cold_open_completed_at';
const _kColdOpenSkipped = 'cold_open_skipped';

class OnboardingService {
  final SharedPreferences _prefs;

  OnboardingService(this._prefs);

  bool get hasSeenColdOpen => _prefs.getBool(_kHasSeenColdOpen) ?? false;

  bool get coldOpenSkipped => _prefs.getBool(_kColdOpenSkipped) ?? false;

  String? get coldOpenCompletedAt => _prefs.getString(_kColdOpenCompletedAt);

  Future<void> markColdOpenCompleted() async {
    await _prefs.setBool(_kHasSeenColdOpen, true);
    await _prefs.setBool(_kColdOpenSkipped, false);
    await _prefs.setString(
      _kColdOpenCompletedAt,
      DateTime.now().toIso8601String(),
    );
  }

  Future<void> markColdOpenSkipped() async {
    await _prefs.setBool(_kHasSeenColdOpen, true);
    await _prefs.setBool(_kColdOpenSkipped, true);
    await _prefs.setString(
      _kColdOpenCompletedAt,
      DateTime.now().toIso8601String(),
    );
  }

  Future<void> resetColdOpen() async {
    await _prefs.remove(_kHasSeenColdOpen);
    await _prefs.remove(_kColdOpenCompletedAt);
    await _prefs.remove(_kColdOpenSkipped);
  }
}

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('Must be overridden at app startup');
});

final onboardingServiceProvider = Provider<OnboardingService>((ref) {
  return OnboardingService(ref.watch(sharedPreferencesProvider));
});
