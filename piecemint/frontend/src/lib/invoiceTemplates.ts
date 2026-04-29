import type { InvoiceExportConfig } from '../types/invoiceExport';
import { createLineItem, defaultInvoiceDocument, defaultParty } from '../types/invoiceDocument';

export type InvoiceTemplateId =
  | 'blank'
  | 'consulting_hours'
  | 'product_sale'
  | 'retainer'
  | 'services_fixed';

export const INVOICE_TEMPLATES: { id: InvoiceTemplateId; label: string; hint: string }[] = [
  { id: 'blank', label: 'Blank', hint: 'Reset document fields' },
  { id: 'consulting_hours', label: 'Consulting', hint: 'Hourly consulting line' },
  { id: 'product_sale', label: 'Product sale', hint: 'Qty × unit' },
  { id: 'retainer', label: 'Monthly retainer', hint: 'Fixed fee, 1 month' },
  { id: 'services_fixed', label: 'Project', hint: 'Fixed-scope deliverable' },
];

/** Partial patch to merge into current export config (keeps logo, fonts, format unless overridden). */
export function applyInvoiceTemplate(
  id: InvoiceTemplateId,
  current: InvoiceExportConfig
): Partial<InvoiceExportConfig> {
  const baseDoc = current.document;
  const today = new Date();
  const due = new Date(today);
  due.setDate(due.getDate() + 30);
  const dates = {
    issueDate: today.toISOString().slice(0, 10),
    dueDate: due.toISOString().slice(0, 10),
  };

  switch (id) {
    case 'blank':
      return {
        document: defaultInvoiceDocument(),
      };

    case 'consulting_hours':
      return {
        document: {
          ...baseDoc,
          ...dates,
          lineItems: [
            createLineItem({
              description: 'Professional consulting services',
              quantity: 8,
              unitLabel: 'hours',
              unitPrice: 175,
            }),
          ],
          notes: 'Payment is due within 30 days of the invoice date. Thank you for your business.',
          supplier: {
            ...defaultParty(),
            legalName: baseDoc.supplier.legalName.trim() || 'Your company name',
            email: baseDoc.supplier.email || '',
          },
        },
      };

    case 'product_sale':
      return {
        document: {
          ...baseDoc,
          ...dates,
          lineItems: [
            createLineItem({
              description: 'Product / SKU — describe item',
              quantity: 2,
              unitLabel: 'units',
              unitPrice: 249
            }),
          ],
          notes: 'Prices exclude shipping and tax unless stated on the invoice.',
        },
      };

    case 'retainer':
      return {
        document: {
          ...baseDoc,
          ...dates,
          lineItems: [
            createLineItem({
              description: 'Monthly retainer — ongoing advisory & support',
              quantity: 1,
              unitLabel: 'days',
              unitPrice: 3500,
            }),
          ],
          notes: 'Retainer covers the billing period shown on this invoice.',
        },
        secondaryColor: '#0F6B4F',
      };

    case 'services_fixed':
      return {
        document: {
          ...baseDoc,
          ...dates,
          lineItems: [
            createLineItem({
              description: 'Fixed-scope delivery — milestone / phase 1',
              quantity: 1,
              unitLabel: 'units',
              unitPrice: 12000,
            }),
          ],
          notes: 'Milestone billing per statement of work. Questions: use supplier contact on this invoice.',
        },
      };

    default:
      return {};
  }
}
