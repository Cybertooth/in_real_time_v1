import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../models/story_item.dart';
import '../theme.dart';

class PhotosScreen extends ConsumerStatefulWidget {
  const PhotosScreen({super.key});

  @override
  ConsumerState<PhotosScreen> createState() => _PhotosScreenState();
}

class _PhotosScreenState extends ConsumerState<PhotosScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final galleryAsync = ref.watch(galleryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('PHOTOS'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppTheme.accentNeon,
          labelColor: AppTheme.accentNeon,
          unselectedLabelColor: AppTheme.textMuted,
          tabs: const [
            Tab(text: 'ALL'),
            Tab(text: 'PHOTOS'),
            Tab(text: 'DOCUMENTS'),
          ],
        ),
      ),
      backgroundColor: AppTheme.darkBg,
      body: galleryAsync.when(
        data: (items) {
          final allPhotos = items.where((i) => i.imageUrl != null && i.imageUrl!.isNotEmpty).toList();
          final photos = allPhotos.where((i) => i.tier == 'atmospheric' || i.tier == 'diegetic').toList();
          final documents = allPhotos.where((i) => i.tier == 'document').toList();

          return TabBarView(
            controller: _tabController,
            children: [
              _GalleryGrid(photos: allPhotos),
              _GalleryGrid(photos: photos),
              _GalleryGrid(photos: documents),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, st) => Center(child: Text('Error: $e', style: const TextStyle(color: Colors.redAccent))),
      ),
    );
  }
}

class _GalleryGrid extends StatelessWidget {
  final List<GalleryPhoto> photos;
  const _GalleryGrid({required this.photos});

  @override
  Widget build(BuildContext context) {
    if (photos.isEmpty) {
      return const Center(
        child: Text('No photos here yet.', style: TextStyle(color: AppTheme.textMuted)),
      );
    }

    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 6,
        crossAxisSpacing: 6,
      ),
      itemCount: photos.length,
      itemBuilder: (context, index) {
        final photo = photos[index];
        return GestureDetector(
          onTap: () => _openFullScreen(context, photos, index),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.network(
                  photo.imageUrl!,
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
                if (photo.tier == 'document')
                  Positioned(
                    bottom: 4,
                    right: 4,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(3),
                      ),
                      child: const Text('DOC', style: TextStyle(color: Colors.white70, fontSize: 8, fontWeight: FontWeight.bold)),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _openFullScreen(BuildContext context, List<GalleryPhoto> photos, int initialIndex) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => _FullScreenViewer(photos: photos, initialIndex: initialIndex),
        fullscreenDialog: true,
      ),
    );
  }
}

class _FullScreenViewer extends StatefulWidget {
  final List<GalleryPhoto> photos;
  final int initialIndex;
  const _FullScreenViewer({required this.photos, required this.initialIndex});

  @override
  State<_FullScreenViewer> createState() => _FullScreenViewerState();
}

class _FullScreenViewerState extends State<_FullScreenViewer> {
  late PageController _pageController;
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final photo = widget.photos[_currentIndex];
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          photo.subject,
          style: const TextStyle(color: Colors.white, fontSize: 14),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: _TierBadge(tier: photo.tier),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _pageController,
              itemCount: widget.photos.length,
              onPageChanged: (i) => setState(() => _currentIndex = i),
              itemBuilder: (context, index) {
                final p = widget.photos[index];
                return InteractiveViewer(
                  child: Center(
                    child: Image.network(
                      p.imageUrl!,
                      fit: BoxFit.contain,
                      errorBuilder: (ctx, err, stack) => const Icon(Icons.broken_image, color: Colors.white24, size: 64),
                    ),
                  ),
                );
              },
            ),
          ),
          if (photo.caption != null && photo.caption!.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              color: Colors.black87,
              child: Text(
                photo.caption!,
                style: const TextStyle(color: Colors.white70, fontSize: 13, fontStyle: FontStyle.italic),
                textAlign: TextAlign.center,
              ),
            ),
          // Page indicator dots
          if (widget.photos.length > 1)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(widget.photos.length, (i) {
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    width: i == _currentIndex ? 10 : 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: i == _currentIndex ? AppTheme.accentNeon : Colors.white24,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  );
                }),
              ),
            ),
        ],
      ),
    );
  }
}

class _TierBadge extends StatelessWidget {
  final String tier;
  const _TierBadge({required this.tier});

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (tier) {
      case 'atmospheric':
        color = Colors.blue.shade300;
        break;
      case 'document':
        color = Colors.amber.shade300;
        break;
      default:
        color = AppTheme.accentNeon;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        border: Border.all(color: color.withOpacity(0.5)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        tier.toUpperCase(),
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1),
      ),
    );
  }
}
