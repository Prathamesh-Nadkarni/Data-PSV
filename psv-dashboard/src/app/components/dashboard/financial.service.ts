// financial.service.ts
import { Injectable } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { map } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class FinancialService {
  constructor(private apiService: ApiService) {}

  getData() {
    return this.apiService.get<any>('analyze_transactions')
      .pipe(
        map(response => {
          return response;
        })
      );
  }
}
