import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { PrimeIcons } from 'primeng/api';

@Component({
  selector: 'app-add',
  templateUrl: './add.component.html',
  styleUrls: ['./add.component.css'],
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
})
export class AddComponent {
  productForm: FormGroup;
  successMessage: string = '';
  errorMessage: string = '';
  PrimeIcons = PrimeIcons;
  
  fields = [
    { name: 'transaction_id', label: 'Transaction ID', type: 'text' },
    { name: 'date', label: 'Date', type: 'date' },
    { name: 'product_category', label: 'Product Category', type: 'select', options: ['Electronics', 'Clothing', 'Books', 'Other'] },
    { name: 'product_name', label: 'Product Name', type: 'text' },
    { name: 'units_sold', label: 'Units Sold', type: 'number', step: 1 },
    { name: 'unit_price', label: 'Unit Price', type: 'number', step: '0.01' },
    { name: 'total_revenue', label: 'Total Revenue', type: 'number', step: '0.01' },
    { name: 'region', label: 'Region', type: 'select', options: ['North', 'South', 'East', 'West'] },
    { name: 'payment_method', label: 'Payment Method', type: 'select', options: ['Credit Card', 'Cash', 'Online', 'Other'] },
  ];

  constructor(private fb: FormBuilder) {
    this.productForm = this.fb.group({
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

  getFieldIcon(fieldName: string): string {
    const iconMap: { [key: string]: string } = {
      transaction_id: 'pi pi-hashtag',
      date: 'pi pi-calendar',
      product_category: 'pi pi-tag',
      product_name: 'pi pi-box',
      units_sold: 'pi pi-shopping-cart',
      unit_price: 'pi pi-dollar',
      total_revenue: 'pi pi-wallet',
      region: 'pi pi-map-marker',
      payment_method: 'pi pi-credit-card'
    };
    return iconMap[fieldName] || 'pi pi-pencil';
  }

  onSubmit() {
    if (this.productForm.valid) {
      // Handle form submission, e.g., send to backend
      console.log(this.productForm.value);
      this.successMessage = 'Product sale added successfully!';
      this.errorMessage = '';
      // Reset form after submission
      this.productForm.reset();
      // Clear success message after 3 seconds
      setTimeout(() => {
        this.successMessage = '';
      }, 3000);
    } else {
      this.errorMessage = 'Please fill out all required fields correctly.';
      this.successMessage = '';
    }
  }
}
