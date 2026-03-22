import 'package:flutter/material.dart';
import '../theme.dart';
import 'journal_screen.dart';
import 'conversations_screen.dart';
import 'email_screen.dart';
import 'files_screen.dart';
import 'contacts_screen.dart';
import 'photos_screen.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';

class HubScreen extends ConsumerWidget {
  const HubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progressAsync = ref.watch(readingProgressProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('TERMINAL'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'ACTIVE SYSTEMS',
                  style: TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2.0,
                  ),
                ),
                progressAsync.when(
                  data: (progress) {
                    return Row(
                      children: [
                        SizedBox(
                          width: 80,
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: progress,
                              backgroundColor: Colors.white10,
                              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.accentNeon),
                              minHeight: 4,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${(progress * 100).toInt()}%',
                          style: const TextStyle(
                            color: AppTheme.accentNeon,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ],
                    );
                  },
                  loading: () => const SizedBox(width: 80, child: LinearProgressIndicator(minHeight: 4, backgroundColor: Colors.transparent)),
                  error: (_, __) => const SizedBox.shrink(),
                ),
              ],
            ),
            const SizedBox(height: 24),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                children: [
                  _HubTile(
                    title: 'JOURNALS',
                    icon: Icons.auto_stories,
                    color: AppTheme.journalColor,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const JournalScreen()),
                    ),
                  ),
                  _HubTile(
                    title: 'MESSAGES',
                    icon: Icons.chat_bubble_rounded,
                    color: AppTheme.chatColor,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const ConversationsScreen()),
                    ),
                  ),
                  _HubTile(
                    title: 'INBOX',
                    icon: Icons.email_rounded,
                    color: AppTheme.emailColor,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const EmailScreen()),
                    ),
                  ),
                  _HubTile(
                    title: 'FILES',
                    icon: Icons.folder_zip_rounded,
                    color: AppTheme.voiceNoteColor,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const FilesScreen()),
                    ),
                  ),
                  _HubTile(
                    title: 'CONTACTS',
                    icon: Icons.contacts_rounded,
                    color: Colors.blueAccent,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const ContactsScreen()),
                    ),
                  ),
                  _HubTile(
                    title: 'PHOTOS',
                    icon: Icons.photo_library_rounded,
                    color: Colors.pinkAccent,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const PhotosScreen()),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HubTile extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _HubTile({
    required this.title,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(4),
      child: Container(
        decoration: AppTheme.cardDecoration(accentBorder: color),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 12),
            Text(
              title,
              style: TextStyle(
                color: color.withOpacity(0.8),
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
