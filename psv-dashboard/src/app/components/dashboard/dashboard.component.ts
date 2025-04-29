import { Component, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts';
import { TableModule } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { TabViewModule } from 'primeng/tabview';
import { DropdownModule } from 'primeng/dropdown';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { FinancialService } from './financial.service';
import { ProductService, Product, ProductSales, PlatformData, CountryPlatformData } from './product.service';
import { ChartConfiguration } from 'chart.js';
import { Pipe, PipeTransform } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { NgSwitch } from '@angular/common';
import { finalize } from 'rxjs/operators';
import { forkJoin } from 'rxjs';
import { ProductDropdownComponent } from '../product-dropdown/product-dropdown.component';
import { SalesDialogComponent } from './sales-dialog/sales-dialog.component';
import { ButtonModule } from 'primeng/button';
import { RippleModule } from 'primeng/ripple';
import { DialogModule } from 'primeng/dialog';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';


@Pipe({ name: 'chartData', standalone: true })
export class ChartDataPipe implements PipeTransform {
  transform(value: { [key: string]: number }): { labels: string[], datasets: any[] } {
    return {
      labels: Object.keys(value),
      datasets: [{
        data: Object.values(value),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
        hoverBackgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']}]
    };
  }
}

interface ChartStates {
  category: 'expanded' | 'collapsed';
  trends: 'expanded' | 'collapsed';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    NgChartsModule,
    TableModule,
    CardModule,
    ChartDataPipe,
    TabViewModule,
    DropdownModule,
    AutoCompleteModule,
    ProgressSpinnerModule,
    NgSwitch,
    ProductDropdownComponent,
    SalesDialogComponent,
    ButtonModule,
    RippleModule,
    DialogModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  animations: [
    trigger('slide', [
      state('collapsed', style({ height: '0', opacity: 0 })),
      state('expanded', style({ height: '*', opacity: 1 })),
      transition('* <=> *', animate('300ms ease-in-out'))
    ])
  ]
})

export class DashboardComponent implements OnInit {
  @ViewChild('salesDialog') salesDialog!: SalesDialogComponent;

  // Financial chart options
  public barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    scales: { x: { stacked: true }, y: { stacked: true } },
    plugins: {
      legend: {
        display: false
      }
    }
  };

  public lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    elements: { line: { tension: 0.5 } },
    plugins: {
      legend: {
        display: false
      }
    }
  };

  chartStates = {
    category: 'expanded',
    trends: 'expanded'
  };

  socialAnalytics: any;
  transactionAnalytics: any;
  userDataAnalytics: any;

  // Financial data
  spendingByCategory: { [key: string]: number } = {};
  monthlyTrends: { [key: string]: number } = {};
  accountAnalysis: { [key: string]: { count: number, total: number } } = {};
  topTransactions: any[] = [];
  sortField = 'type';
  sortOrder = 1;
  accountData: any[] = [];
  selectedProduct: Product | null = null;
  selectedProductSales: ProductSales | null = null;

  // Product data
  products: Product[] = [];
  filteredProducts: Product[] = [];
  productSales: ProductSales[] = [];
  salesByCountry: { [key: string]: number } = {};
  salesByCategory: { [key: string]: number } = {};
  totalSales: number = 0;
  totalQuantity: number = 0;
  loading = false;
  availableCountryOptions: { label: string, value: string }[] = [];
  showSalesDialog = false;

  // Forecasting data
  selectedForecastProduct: Product | null = null;
  countryPlatformData: CountryPlatformData = {};
  availableCountries: any[] = [];
  selectedCountry: string | null = null;
  platformDataForChart: PlatformData[] = [];
  loadingForecast = false;
  chartColors: string[] = [
    '#4CAF50', // Green
    '#2196F3', // Blue
    '#FFC107', // Amber
    '#9C27B0', // Purple
    '#FF5722', // Deep Orange
    '#607D8B', // Blue Grey
    '#009688', // Teal
    '#E91E63', // Pink
    '#673AB7', // Deep Purple
    '#3F51B5'  // Indigo
  ];

  // Pie chart options
  public pieChartOptions: ChartConfiguration<'pie'>['options'] = {
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.formattedValue;
            const percentage = context.raw as number;
            return `${label}: ${value} (${percentage.toFixed(1)}%)`;
          }
        }
      }
    }
  };

  constructor(
    private financialService: FinancialService,
    private productService: ProductService,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    // Load financial data
    this.loadFinancialData();

    // Load product list
    this.loadProducts();
    this.loadAnalytics();
  }

  goToPredictor() {
    this.router.navigate(['/predictor']);
  }

  loadAnalytics() {
    this.apiService.getSocialAnalytics().subscribe(data => {
      this.socialAnalytics = data;
    });

    this.apiService.getTransactionAnalytics().subscribe(data => {
      this.transactionAnalytics = data;
    });

    this.apiService.getUserDataAnalytics().subscribe(data => {
      this.userDataAnalytics = data;
    });
  }


  // Open sales dialog method
  openSalesDialog() {
    console.log('Opening sales dialog...');
    this.showSalesDialog = true;
    
    // Use requestAnimationFrame to ensure the dialog is properly rendered
    requestAnimationFrame(() => {
      if (this.salesDialog) {
        console.log('Calling show() on dialog component');
        this.salesDialog.show();
      } else {
        console.error('Sales dialog component not found');
      }
    });
  }



  onSalesDialogSubmit(event: any) {
    console.log('Sales dialog submit success:', event);
    this.showSalesDialog = false;
    if (this.selectedProduct?.product_name) {
      this.fetchProductSalesData(this.selectedProduct.product_name);
    }
  }

  onSalesDialogCancel() {
    this.showSalesDialog = false;
  }

  loadFinancialData() {
    this.financialService.getData().subscribe((response: any) => {
      this.spendingByCategory = {};
      this.monthlyTrends = {};
      this.accountAnalysis = {};
      this.topTransactions = [];
      this.accountData = [];

      if (response) {
        this.spendingByCategory = response.spending_by_category || {};
        this.monthlyTrends = response.monthly_trends || {};
        this.accountAnalysis = response.account_type_analysis || {};
        this.topTransactions = response.top_transactions || [];

        this.accountData = Object.entries(this.accountAnalysis).map(([type, value]: [string, any]) => ({
          type,
          count: value.count,
          total: value.total
        }));
      } else {
        console.error('Invalid API response:', response);
      }
    }, error => {
      console.error('API Error:', error);
    });
  }

  loadProducts() {
    this.loading = true;
    console.log('Loading products - starting request...');

    this.productService.getProducts().subscribe({
      next: (products: Product[]) => {
        this.products = products.filter(product =>
          product?.product_name?.trim()
        );
        this.filteredProducts = [...this.products];
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading products:', error);
        this.products = [];
        this.filteredProducts = [];
        this.loading = false;
      }
    });
  }

  // Updated filter method
  filterProducts(event: any) {
    const query = (event.query || '').toLowerCase().trim();
    this.filteredProducts = this.products.filter(product =>
      product.product_name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .includes(query)
    );
  }

  onProductSelected(productName: string): void {
    console.log(`Product selected: ${productName}`);
    if (!productName) {
      // Clear previous data if no product is selected
      this.productSales = [];
      this.salesByCountry = {};
      this.salesByCategory = {};
      this.totalSales = 0;
      this.totalQuantity = 0;
      return;
    }
    this.selectedProduct = { product_name: productName } as Product;
    this.fetchProductSalesData(productName);
  }

  // Fetch sales data when a product is selected
  fetchProductSalesData(productName: string): void {
    if (!productName || productName.trim() === '') {
      console.log('Invalid product name');
      return;
    }

    console.log(`Fetching sales data for: ${productName}`);
    this.loading = true;

    // Load sales data for the selected product
    this.productService.getSalesByProduct(productName)
      .pipe(finalize(() => {
        this.loading = false;
        console.log('Sales data loading completed');
      }))
      .subscribe({
        next: (sales: ProductSales[]) => {
          console.log(`Received sales data (${sales.length} records)`);
          this.productSales = sales;
          this.processSalesData(sales);
        },
        error: (error: any) => {
          console.error('Error loading product sales data:', error);
          this.productSales = [];
          this.salesByCountry = {};
          this.salesByCategory = {};
          this.totalSales = 0;
          this.totalQuantity = 0;
        }
      });
  }

  /**
   * Process sales data to calculate totals and group by country and category
   */
  processSalesData(sales: ProductSales[]) {
    this.salesByCountry = {};
    this.salesByCategory = {};
    this.totalSales = 0;
    this.totalQuantity = 0;

    sales.forEach(item => {
      // Aggregate by country
      if (!this.salesByCountry[item.country]) {
        this.salesByCountry[item.country] = 0;
      }
      this.salesByCountry[item.country] += item.sales;

      // Aggregate by category
      if (!this.salesByCategory[item.category]) {
        this.salesByCategory[item.category] = 0;
      }
      this.salesByCategory[item.category] += item.sales;

      // Calculate totals
      this.totalSales += item.sales;
      this.totalQuantity += item.quantity;
    });
  }

  toggleChart(chartType: keyof ChartStates) {
    this.chartStates[chartType] =
      this.chartStates[chartType] === 'expanded' ? 'collapsed' : 'expanded';
  }

  onSort(event: any) {
    this.sortField = event.field;
    this.sortOrder = event.order;
  }

  // Handle product selection in forecasting tab
  onForecastProductSelected(productName: string): void {
    console.log(`Forecast product selected: ${productName}`);
    if (!productName) {
      this.countryPlatformData = {};
      this.availableCountries = [];
      this.selectedCountry = '';
      this.platformDataForChart = [];
      return;
    }
    this.selectedForecastProduct = { product_name: productName } as Product;
    this.fetchPlatformData(productName);
  }

  // Fetch platform data for forecasting
  fetchPlatformData(productId: string) {
    this.productService.getBestPlatform(productId).subscribe(data => {
      this.countryPlatformData = data;
      this.availableCountries = Object.keys(data);
      this.availableCountries = Object.keys(data);

      this.availableCountryOptions = this.availableCountries.map(c => ({
        label: c,
        value: c
      }));

      // Only reset selectedCountry if it's not set or not in the new list
      if (!this.selectedCountry || !this.availableCountries.includes(this.selectedCountry)) {
        this.selectedCountry = this.availableCountries[0];
      }

      this.updatePlatformDataForChart();
    });

  }


  // Handle country selection change
  onCountryChange(event: any): void {
    console.log('Country changed:', event);
    this.selectedCountry = event.value;
    this.updatePlatformDataForChart();
  }

  // Update the chart data when country changes
  updatePlatformDataForChart(): void {
    console.log('Updating platform data for country:', this.selectedCountry);

    if (!this.selectedCountry || !this.countryPlatformData[this.selectedCountry]) {
      console.warn('No platform data available for selected country');
      this.platformDataForChart = [];
      return;
    }

    const countryData = this.countryPlatformData[this.selectedCountry];
    console.log('Country data:', countryData);

    // Convert the country data to an array of PlatformData
    this.platformDataForChart = Object.entries(countryData).map(([platform, percentage]) => ({
      platform,
      percentage
    }));

    console.log('Updated platform data for chart:', this.platformDataForChart);
  }

  // Prepare platform data for pie chart
  getPlatformChartData() {
    if (!this.platformDataForChart || this.platformDataForChart.length === 0) {
      return {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: []
        }]
      };
    }

    return {
      labels: this.platformDataForChart.map(item => item.platform),
      datasets: [{
        data: this.platformDataForChart.map(item => item.percentage),
        backgroundColor: this.chartColors.slice(0, this.platformDataForChart.length)
      }]
    };
  }
}
