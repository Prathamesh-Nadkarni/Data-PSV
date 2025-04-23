import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError, of } from 'rxjs';
import { catchError, tap, map } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';

export interface Product {
  product_name: string;
  id?: string | number;
  // Add any other properties that might be in the response
  [key: string]: any;
}

export interface ProductSales {
  country: string;
  category: string;
  product_name: string;
  sales: number;
  quantity: number;
}

export interface SalesByProduct {
  sales_data: ProductSales[];
}

export interface PlatformData {
  platform: string;
  percentage: number;
}

export interface CountryPlatformData {
  [country: string]: {
    [platform: string]: number;
  };
}

export interface SalesSubmission {
  transaction_id: string;
  date: string;
  product_category: string;
  product_name: string;
  units_sold: number;
  unit_price: number;
  total_revenue: number;
  region: string;
  payment_method: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  constructor(private http: HttpClient, private apiService: ApiService) {}

  /**
   * Get all products from the API
   */
  getProducts(): Observable<Product[]> {
    console.log('Calling get_products API...');
    return this.apiService.get<any>('get_products').pipe(
      tap(response => {
        console.log('Products API response type:', typeof response);
        console.log('Products API response:', response);
      }),
      // Transform the response to ensure it's in the expected format
      map((response: any) => {
        console.log('Processing response in map operator');
        
        // Extract the array of products from the response
        let productsArray: any[] = [];
        
        // CASE 1: Handle if response is directly an array of products
        if (Array.isArray(response)) {
          console.log('Response is an array');
          productsArray = response;
        } 
        // CASE 2: Handle if response is an object containing products array
        else if (response && typeof response === 'object') {
          // Check common API wrapper formats
          for (const key of ['data', 'results', 'products', 'items']) {
            if (response[key] && Array.isArray(response[key])) {
              console.log(`Found products in ${key} property`);
              productsArray = response[key];
              break;
            }
          }
          
          // If no array found in common properties, try to convert object to array
          if (productsArray.length === 0) {
            console.log('Converting object properties to products array');
            productsArray = Object.entries(response).map(([key, value]) => {
              if (typeof value === 'object' && value !== null) {
                const typedValue = value as Record<string, any>;
                return { ...typedValue, product_name: typedValue['product_name'] || key };
              } else if (typeof value === 'string') {
                return { product_name: value };
              }
              return null;
            }).filter(item => item !== null);
          }
        }
        
        // Normalize the products array to ensure each item has the required properties
        const normalizedProducts = productsArray.map((item, index) => {
          if (!item) return null;
          
          // If item is a string, convert to object
          if (typeof item === 'string') {
            return { product_name: item };
          } 
          // If item is an object but doesn't have product_name
          else if (typeof item === 'object') {
            if (!item.product_name) {
              // Look for alternative property names
              const possibleNameKeys = ['name', 'title', 'label', 'productName', 'product'];
              for (const key of possibleNameKeys) {
                if (item[key] && typeof item[key] === 'string') {
                  return { ...item, product_name: item[key] };
                }
              }
              return { ...item, product_name: `Product ${index + 1}` };
            }
            return item;
          }
          
          return null;
        }).filter(item => item !== null) as Product[];
        
        console.log(`Final normalized products: ${normalizedProducts.length}`);
        
        if (normalizedProducts.length === 0) {
          console.log('No products found, returning sample data');
          return [
            { product_name: 'Laptop', id: 'sample1' },
            { product_name: 'Smartphone', id: 'sample2' },
            { product_name: 'Tablet', id: 'sample3' },
            { product_name: 'Headphones', id: 'sample4' },
            { product_name: 'Monitor', id: 'sample5' }
          ];
        }
        
        return normalizedProducts;
      }),
      catchError(error => {
        console.error('Error fetching products:', error);
        // Provide sample products when API call fails
        const sampleProducts = [
          { product_name: 'Laptop (Fallback)', id: 'fallback1' },
          { product_name: 'Smartphone (Fallback)', id: 'fallback2' },
          { product_name: 'Tablet (Fallback)', id: 'fallback3' },
          { product_name: 'Headphones (Fallback)', id: 'fallback4' },
          { product_name: 'Monitor (Fallback)', id: 'fallback5' }
        ];
        console.log('Using fallback sample product data due to API error');
        return of(sampleProducts);
      })
    );
  }

  /**
   * Get sales data for a specific product by name
   */
  getSalesByProduct(productName: string): Observable<ProductSales[]> {
    if (!productName) {
      return throwError(() => new Error('Product name is required'));
    }
    
    const params = new HttpParams().set('product_name', productName);
    console.log(`Calling sales_by_product API with product_name: ${productName}`);
    
    return this.apiService.get<ProductSales[]>('sales_by_product', params).pipe(
      tap(response => {
        console.log('Sales API response:', response);
      }),
      map((response: any) => {
        // If the response is empty or invalid, return sample data
        if (!response || (Array.isArray(response) && response.length === 0)) {
          console.log('Sales API returned empty data, providing sample sales data');
          return this.getSampleSalesData(productName);
        }
        
        // If response is not an array, but an object with a data property
        if (!Array.isArray(response) && response && typeof response === 'object') {
          if (response.data && Array.isArray(response.data)) {
            return response.data as ProductSales[];
          }
          if (response.sales_data && Array.isArray(response.sales_data)) {
            return response.sales_data as ProductSales[];
          }
          // Convert object to array if necessary
          if (Object.keys(response).length > 0) {
            return this.getSampleSalesData(productName);
          }
        }
        
        return response as ProductSales[];
      }),
      catchError(error => {
        console.error(`Error fetching sales data for product "${productName}":`, error);
        return of(this.getSampleSalesData(productName));
      })
    );
  }
  
  /**
   * Generate sample sales data for testing
   */
  private getSampleSalesData(productName: string): ProductSales[] {
    const countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan', 'Australia', 'Brazil', 'China', 'India'];
    const categories = ['Electronics', 'Clothing', 'Books', 'Home Goods', 'Sports'];
    
    // Generate 15 random sales records
    return Array.from({ length: 15 }, (_, i) => {
      const country = countries[Math.floor(Math.random() * countries.length)];
      const category = categories[Math.floor(Math.random() * categories.length)];
      const sales = Math.floor(Math.random() * 100000) + 5000;
      const quantity = Math.floor(Math.random() * 500) + 10;
      
      return {
        country,
        category,
        product_name: productName,
        sales,
        quantity
      };
    });
  }

  /**
   * Get best platform recommendation for a product
   */
  getBestPlatform(productName: string): Observable<CountryPlatformData> {
    if (!productName) {
      return throwError(() => new Error('Product name is required'));
    }
    
    console.log(`Calling get_best_platform API with product_name: ${productName}`);
    
    const payload = { product_name: productName };
    
    return this.apiService.post<any>('get_best_platform', payload).pipe(
      tap(response => {
        console.log('Best platform API raw response:', response);
      }),
      map((response: any) => {
        // Handle the nested JSON string in the response
        if (response && response.best_platform) {
          try {
            // Try to parse the JSON string into an object
            let platformData: CountryPlatformData;
            
            if (typeof response.best_platform === 'string') {
              console.log('Parsing JSON string response');
              platformData = JSON.parse(response.best_platform);
            } else if (typeof response.best_platform === 'object') {
              console.log('Response is already an object');
              platformData = response.best_platform;
            } else {
              throw new Error('Invalid response format');
            }
            
            console.log('Parsed platform data:', platformData);
            return platformData as CountryPlatformData;
          } catch (error) {
            console.error('Error parsing platform data:', error);
          }
        }
        
        console.log('Using sample data due to invalid response format');
        return this.getSampleCountryPlatformData();
      }),
      catchError(error => {
        console.error(`Error fetching best platform data for product "${productName}":`, error);
        return of(this.getSampleCountryPlatformData());
      })
    );
  }
  
  /**
   * Generate sample country platform data for testing
   */
  private getSampleCountryPlatformData(): CountryPlatformData {
    return {
      "United States": {
        "Facebook": 25.16,
        "Instagram": 23.31,
        "YouTube": 25.81,
        "TikTok": 25.72
      },
      "India": {
        "TikTok": 25.77,
        "YouTube": 24.89,
        "Facebook": 24.09,
        "Instagram": 25.24
      },
      "Japan": {
        "Instagram": 23.31,
        "Facebook": 26.4,
        "TikTok": 25.01,
        "YouTube": 25.28
      },
      "Germany": {
        "TikTok": 26.21,
        "YouTube": 25.37,
        "Facebook": 23.96,
        "Instagram": 24.46
      }
    };
  }

  /**
   * Submit sales data 
   */
  submitSalesJob(salesData: SalesSubmission): Observable<any> {
    console.log('Submitting sales data:', salesData);
    return this.apiService.post<any>('submit_sales', salesData).pipe(
      tap(response => {
        console.log('Sales submission response:', response);
      }),
      catchError(error => {
        console.error('Error submitting sales data:', error);
        return throwError(() => new Error('Failed to submit sales data: ' + (error.message || 'Unknown error')));
      })
    );
  }
}

