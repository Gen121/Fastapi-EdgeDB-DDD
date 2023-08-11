module default {
    type OrderLine {
        orderid: str {
            constraint max_len_value(255);
        };
        sku: str {constraint max_len_value(255)};
        required qty: int16;
        allocated_in: Batch;
    };

    type Batch {
        reference: str {
            constraint max_len_value(255);
            constraint exclusive
        };
        sku: str {constraint max_len_value(255)};
        product: Product {
            rewrite insert, update using (
                (SELECT Product filter .sku = __subject__.sku)
            )
        };
        eta: cal::local_date;
        required purchased_quantity: int16;
        multi link allocations := .<allocated_in[is OrderLine];
    };

    type Product {
        required sku: str {
            constraint max_len_value(255);
            constraint exclusive
        };
        required version_number: int16;
        multi link batches := .<product[is Batch];
    };

    type AllocationsView {
        orderid: str {constraint max_len_value(255)};
        sku: str {constraint max_len_value(255)};
        batchref: str {constraint max_len_value(255)};
    };
}