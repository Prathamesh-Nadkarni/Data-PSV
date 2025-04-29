import { Component } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-predictor',
  templateUrl: './predictor.component.html',
  styleUrls: ['./predictor.component.css'],
  imports: [HttpClientModule, FormsModule, CommonModule]
})
export class PredictorComponent {
  input = {
    country: '',
    category: '',
    product_name: '',
    sales: 0
  };

  predictionResult: any = null;

  countries = [
    'USA', 'Canada', 'Germany', 'India', 'Brazil',
    'United Kingdom', 'France', 'Australia', 'Japan', 'South Korea'
  ];

  constructor(private apiService: ApiService) {}
  categories: string[] = [];
  products: string[] = [];

ngOnInit(): void {
  this.apiService.getCategories().subscribe(data => {
    this.categories = data;
  });
}

onCategoryChange() {
  if (this.input.category) {
    this.apiService.getProductsByCategory(this.input.category).subscribe(data => {
      this.products = data;
      this.input.product_name = ''; // reset product selection
    });
  } else {
    this.products = [];
  }
}

  predict() {
    this.apiService.predictQuantity(this.input).subscribe(result => {
      const quantity = result.predicted_quantity;
      this.predictionResult = {
        predicted_quantity: quantity,
        predicted_sales: quantity * this.input.sales
      };
    }, error => {
      this.predictionResult = { error: 'Prediction failed.' };
    });
  }
}
