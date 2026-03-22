import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';

class PhotosScreen extends ConsumerWidget {
  const PhotosScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storyItemsAsync = ref.watch(storyItemsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('PHOTOS'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
      ),
      backgroundColor: AppTheme.darkBg,
      body: storyItemsAsync.when(
        data: (items) {
          final photoItems = items.where((i) => !i.isLocked && i.imageUrl != null && i.imageUrl!.isNotEmpty).toList();
          
          if (photoItems.isEmpty) {
            return const Center(child: Text('No photos available.', style: TextStyle(color: AppTheme.textMuted)));
          }

          return GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
            ),
            itemCount: photoItems.length,
            itemBuilder: (context, index) {
              final item = photoItems[index];
              return ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  item.imageUrl!,
                  fit: BoxFit.cover,
                  errorBuilder: (ctx, err, stack) => Container(
                    color: Colors.white10,
                    child: const Icon(Icons.broken_image, color: Colors.white24),
                  ),
                  loadingBuilder: (ctx, child, progress) {
                    if (progress == null) return child;
                    return Container(
                      color: Colors.white10,
                      child: const Center(
                        child: CircularProgressIndicator(color: AppTheme.accentNeon, strokeWidth: 2),
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, st) => Center(child: Text('Error: $e', style: const TextStyle(color: Colors.redAccent))),
      ),
    );
  }
}
