import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Observable, startWith, map, of } from 'rxjs';
import { ProductService, Product } from '../dashboard/product.service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';

@Component({
  selector: 'app-product-dropdown',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatAutocompleteModule
  ],
  template: `
    <mat-form-field class="full-width" appearance="fill">
      <mat-label>Select a product</mat-label>
      <input
        type="text"
        matInput
        [formControl]="productControl"
        [matAutocomplete]="auto"
        [placeholder]="'Start typing product name'"
      />
      <mat-autocomplete #auto="matAutocomplete" (optionSelected)="onSelectionChange($event)">
        <mat-option *ngFor="let option of filteredProducts$ | async" [value]="option">
          {{ option }}
        </mat-option>
      </mat-autocomplete>
    </mat-form-field>
  `,
  styles: [`
    .full-width {
      width: 100%;
    }
  `]
})
export class ProductDropdownComponent implements OnInit {
  @Output() productSelected = new EventEmitter<string>();
  
  productControl = new FormControl('');
  filteredProducts$!: Observable<string[]>;
  allProductNames: string[] = [];

  constructor(private productService: ProductService) {}

  ngOnInit(): void {
    this.productService.getProducts().subscribe({
      next: (products: Product[]) => {
        this.allProductNames = products.map(p => p.product_name?.replace(/^"+|"+$/g, '') || '');
        this.setupFilter();
      },
      error: err => {
        console.error('Error loading products:', err);
        this.allProductNames = [];
        this.setupFilter();
      }
    });
    
    // Also emit selection when value changes directly in the form control
    this.productControl.valueChanges.subscribe(value => {
      if (value && this.allProductNames.includes(value)) {
        this.productSelected.emit(value);
      }
    });
  }

  onSelectionChange(event: any): void {
    const value = event.option.value;
    if (value) {
      this.productSelected.emit(value);
    }
  }

  private setupFilter(): void {
    this.filteredProducts$ = this.productControl.valueChanges.pipe(
      startWith(''),
      map(input => this.filterProducts(input || ''))
    );
  }

  private filterProducts(input: string): string[] {
    const filterValue = input.toLowerCase();
    return this.allProductNames.filter(name => name.toLowerCase().includes(filterValue));
  }
}
