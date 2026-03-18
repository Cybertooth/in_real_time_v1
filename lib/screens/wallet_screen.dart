import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../models/story_item.dart';

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
            return const Center(child: Text('No transactions found.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: receipts.length,
            itemBuilder: (context, index) {
              final receipt = receipts[index];
              return _buildReceiptCard(receipt);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Widget _buildReceiptCard(Receipt receipt) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: const Border(
          left: BorderSide(color: AppTheme.accentNeon, width: 4),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
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
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  receipt.description,
                  style: const TextStyle(color: AppTheme.textDim, fontSize: 12),
                ),
                Text(
                  DateFormat('yyyy-MM-dd HH:mm').format(receipt.unlockTimestamp),
                  style: const TextStyle(color: AppTheme.textDim, fontSize: 10),
                ),
              ],
            ),
          ),
          Text(
            '\$${receipt.amount.toStringAsFixed(2)}',
            style: const TextStyle(
              color: AppTheme.accentNeon,
              fontWeight: FontWeight.bold,
              fontSize: 18,
              fontFamily: 'Courier',
            ),
          ),
        ],
      ),
    );
  }
}
