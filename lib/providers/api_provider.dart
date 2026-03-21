import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider for the backend base URL.
final backendUrlProvider = StateNotifierProvider<BackendUrlNotifier, String>((ref) {
  return BackendUrlNotifier();
});

class BackendUrlNotifier extends StateNotifier<String> {
  BackendUrlNotifier() : super('https://python-director-66224741815.us-central1.run.app') {
    _loadUrl();
  }

  static const String _storageKey = 'backend_base_url';

  Future<void> _loadUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_storageKey);
    if (savedUrl != null && savedUrl.isNotEmpty) {
      state = savedUrl;
    }
  }

  Future<void> setUrl(String url) async {
    state = url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, url);
  }
  
  Future<void> resetToDefault() async {
    const defaultUrl = 'https://python-director-66224741815.us-central1.run.app';
    await setUrl(defaultUrl);
  }
}
