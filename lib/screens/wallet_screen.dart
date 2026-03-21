import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';
import '../widgets/shared_widgets.dart';

class WalletScreen extends ConsumerWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final receiptsAsync = ref.watch(receiptProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('WALLET')),
      body: receiptsAsync.when(
        data: (receipts) {
          if (receipts.isEmpty) {
            return const EmptyState(
              icon: Icons.account_balance_wallet_outlined,
              title: 'NO TRANSACTIONS',
              subtitle: 'Intercepted receipts and transactions will appear here.',
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: receipts.length,
            itemBuilder: (context, index) => _buildReceiptCard(context, receipts[index]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildReceiptCard(BuildContext context, Receipt receipt) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(accentBorder: AppTheme.receiptColor),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  receipt.merchantName.toUpperCase(),
                  style: const TextStyle(
                    color: AppTheme.textBody,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 4),
                Text(receipt.description, style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 2),
                TimestampLabel(time: receipt.unlockTimestamp),
              ],
            ),
          ),
          Text(
            '\$${receipt.amount.toStringAsFixed(2)}',
            style: const TextStyle(
              color: AppTheme.accentNeon,
              fontWeight: FontWeight.bold,
              fontSize: 20,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}
