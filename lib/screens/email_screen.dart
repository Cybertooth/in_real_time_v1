import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';

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
            return const Center(child: Text('Empty inbox.'));
          }

          return ListView.separated(
            itemCount: emails.length,
            separatorBuilder: (context, index) => const Divider(
              color: AppTheme.textDim,
              height: 1,
              thickness: 0.2,
            ),
            itemBuilder: (context, index) {
              final email = emails[index];
              return _buildEmailTile(context, email);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildEmailTile(BuildContext context, Email email) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      title: Text(
        email.sender,
        style: const TextStyle(
          color: AppTheme.accentNeon,
          fontWeight: FontWeight.bold,
          fontSize: 14,
        ),
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 4),
          Text(
            email.subject,
            style: const TextStyle(
              color: AppTheme.textBody,
              fontWeight: FontWeight.w500,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            email.body,
            style: const TextStyle(color: AppTheme.textDim, fontSize: 12),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
      trailing: Text(
        DateFormat('HH:mm').format(email.unlockTimestamp),
        style: const TextStyle(color: AppTheme.textDim, fontSize: 10),
      ),
      onTap: () => _showEmailDetail(context, email),
    );
  }

  void _showEmailDetail(BuildContext context, Email email) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Padding(
          padding: const EdgeInsets.all(24.0),
          child: ListView(
            controller: scrollController,
            children: [
              Text(email.subject, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 16),
              Text('From: ${email.sender}', style: const TextStyle(color: AppTheme.accentNeon)),
              Text('Date: ${DateFormat('yyyy-MM-dd HH:mm').format(email.unlockTimestamp)}',
                  style: const TextStyle(color: AppTheme.textDim, fontSize: 12)),
              const Divider(color: AppTheme.accentNeon, height: 32),
              Text(email.body, style: const TextStyle(height: 1.6)),
            ],
          ),
        ),
      ),
    );
  }
}
