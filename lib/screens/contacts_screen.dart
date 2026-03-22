import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';

class ContactsScreen extends ConsumerWidget {
  const ContactsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activeStoryAsync = ref.watch(activeStoryProvider);
    final activeStory = activeStoryAsync.value;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CONTACTS'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
      ),
      backgroundColor: AppTheme.darkBg,
      body: activeStory == null 
          ? const Center(child: Text('No active connection.', style: TextStyle(color: AppTheme.textMuted)))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: activeStory.characters.length,
              itemBuilder: (context, index) {
                final char = activeStory.characters[index];
                final name = char['name'] ?? 'Unknown';
                final background = char['background'] ?? '';
                // Hiding 'arc_summary' to be spoiler-free.

                return Card(
                  color: Colors.white.withOpacity(0.05),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: const BorderSide(color: Colors.white12),
                  ),
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              backgroundColor: AppTheme.accentNeon.withOpacity(0.2),
                              child: Text(
                                name.isNotEmpty ? name[0].toUpperCase() : '?',
                                style: const TextStyle(color: AppTheme.accentNeon, fontWeight: FontWeight.bold),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Text(
                              name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                        if (background.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          const Text('BACKGROUND', style: TextStyle(fontSize: 10, color: AppTheme.accentNeon, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                          const SizedBox(height: 4),
                          Text(
                            background,
                            style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.4),
                          ),
                        ]
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
