  import { CommonModule  } from '@angular/common';
import { Component, EventEmitter, Output, Input, OnChanges, SimpleChanges, ChangeDetectorRef   } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { DatePickerModule } from 'primeng/datepicker';
import { RippleModule } from 'primeng/ripple';
import { ProductService, SalesSubmission } from '../product.service';

@Component({
  selector: 'app-sales-dialog',
  templateUrl: './sales-dialog.component.html',
  styleUrls: ['./sales-dialog.component.css'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    DialogModule,
    ButtonModule,
    InputTextModule,
    InputNumberModule,
    DatePickerModule,
    SelectModule,
    RippleModule
  ],
})
export class SalesDialogComponent {
  @Input() visible: boolean = false;
  @Output() close = new EventEmitter<void>();
  @Output() submitSuccess = new EventEmitter<any>();

  salesForm: FormGroup;
  submitting: boolean = false;
  successMessage: string = '';
  errorMessage: string = '';

  categoryOptions = [
    { label: 'Electronics', value: 'Electronics' },
    { label: 'Clothing', value: 'Clothing' },
    { label: 'Books', value: 'Books' },
    { label: 'Home Goods', value: 'Home Goods' },
    { label: 'Sports', value: 'Sports' },
    { label: 'Other', value: 'Other' }
  ];

  regionOptions = [
    { label: 'North America', value: 'North America' },
    { label: 'South America', value: 'South America' },
    { label: 'Europe', value: 'Europe' },
    { label: 'Asia', value: 'Asia' },
    { label: 'Africa', value: 'Africa' },
    { label: 'Oceania', value: 'Oceania' }
  ];

  paymentOptions = [
    { label: 'Credit Card', value: 'Credit Card' },
    { label: 'Cash', value: 'Cash' },
    { label: 'Online Payment', value: 'Online Payment' },
    { label: 'Bank Transfer', value: 'Bank Transfer' },
    { label: 'Other', value: 'Other' }
  ];

  constructor(
    private fb: FormBuilder,
    private cdRef: ChangeDetectorRef,
    private productService: ProductService
  ) {
    this.salesForm = this.fb.group({
      transaction_id: ['', Validators.required],
      date: ['', Validators.required],
      product_category: ['', Validators.required],
      product_name: ['', Validators.required],
      units_sold: ['', [Validators.required, Validators.min(1)]],
      unit_price: ['', [Validators.required, Validators.min(0)]],
      total_revenue: ['', [Validators.required, Validators.min(0)]],
      region: ['', Validators.required],
      payment_method: ['', Validators.required]
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    console.log('Dialog visibility changed:', changes['visible']);
    if (changes['visible'] && changes['visible'].currentValue) {
      this.salesForm.reset();
      this.successMessage = '';
      this.errorMessage = '';
    }
  }


  show() {
    console.log('SalesDialogComponent show method called');
    this.visible = true;
    this.salesForm.reset();
    this.successMessage = '';
    this.errorMessage = '';
  }

  hide() {
    this.visible = false;
    this.cdRef.detectChanges();
  }

  onSubmit() {
    if (this.salesForm.valid) {
      this.submitting = true;
      this.errorMessage = '';
      const formValues = this.salesForm.value;
      const salesData: SalesSubmission = {
        ...formValues,
        date: formValues.date instanceof Date
          ? formValues.date.toISOString().split('T')[0]
          : String(formValues.date || '')
      };
      this.productService.submitSalesJob(salesData).subscribe({
        next: (response) => {
          this.submitting = false;
          this.successMessage = 'Sales data submitted successfully!';
          this.submitSuccess.emit(response);
          setTimeout(() => {
            this.hide();
            this.successMessage = '';
          }, 2000);
        },
        error: (error) => {
          this.submitting = false;
          this.errorMessage = error.message || 'Failed to submit sales data. Please try again.';
        }
      });
    } else {
      this.errorMessage = 'Please fill out all required fields correctly.';
      Object.keys(this.salesForm.controls).forEach(key => {
        this.salesForm.get(key)?.markAsTouched();
      });
    }
  }
}
