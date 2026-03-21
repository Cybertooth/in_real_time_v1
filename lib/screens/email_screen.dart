import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';
import '../widgets/shared_widgets.dart';

class EmailScreen extends ConsumerWidget {
  const EmailScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final emailsAsync = ref.watch(emailProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('INBOX')),
      body: emailsAsync.when(
        data: (emails) {
          if (emails.isEmpty) {
            return const EmptyState(
              icon: Icons.inbox,
              title: 'EMPTY INBOX',
              subtitle: 'Intercepted emails will appear here.',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: emails.length,
            itemBuilder: (context, index) => _buildEmailTile(context, emails[index]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildEmailTile(BuildContext context, Email email) {
    return InkWell(
      onTap: () => _showEmailDetail(context, email),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.03))),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Sender avatar
            CircleAvatar(
              radius: 16,
              backgroundColor: AppTheme.emailColor.withOpacity(0.1),
              child: Text(
                email.sender.isNotEmpty ? email.sender[0].toUpperCase() : '?',
                style: TextStyle(color: AppTheme.emailColor, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(email.sender, style: TextStyle(color: AppTheme.emailColor, fontWeight: FontWeight.w600, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text(
                    email.subject,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontSize: 14),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(email.body, style: Theme.of(context).textTheme.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
            const SizedBox(width: 8),
            TimestampLabel(time: email.unlockTimestamp, showDate: false),
          ],
        ),
      ),
    );
  }

  void _showEmailDetail(BuildContext context, Email email) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surfaceLow,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Padding(
          padding: const EdgeInsets.all(24.0),
          child: ListView(
            controller: scrollController,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(email.subject, style: Theme.of(context).textTheme.headlineMedium),
                  ),
                  const InterceptedLabel(),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: AppTheme.glassDecoration(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('From: ${email.sender}', style: TextStyle(color: AppTheme.emailColor, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 2),
                    TimestampLabel(time: email.unlockTimestamp),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Text(email.body, style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
        ),
      ),
    );
  }
}
