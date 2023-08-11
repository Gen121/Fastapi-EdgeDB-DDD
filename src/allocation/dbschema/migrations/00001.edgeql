CREATE MIGRATION m1uqgkh6vyciv2dqsr5zg3w3kstlxh2v4zrrlieyeg232giknjakxq
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE TYPE default::Batch {
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE PROPERTY eta: cal::local_date;
      CREATE REQUIRED PROPERTY purchased_quantity: std::int16;
      CREATE PROPERTY reference: std::str {
          CREATE CONSTRAINT std::exclusive;
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  CREATE TYPE default::OrderLine {
      CREATE LINK allocated_in: default::Batch;
      CREATE PROPERTY orderid: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE REQUIRED PROPERTY qty: std::int16;
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  ALTER TYPE default::Batch {
      CREATE MULTI LINK allocations := (.<allocated_in[IS default::OrderLine]);
  };
  CREATE TYPE default::Product {
      CREATE REQUIRED PROPERTY sku: std::str {
          CREATE CONSTRAINT std::exclusive;
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE REQUIRED PROPERTY version_number: std::int16;
  };
  ALTER TYPE default::Batch {
      CREATE LINK product: default::Product {
          CREATE REWRITE
              INSERT 
              USING (SELECT
                  default::Product
              FILTER
                  (.sku = __subject__.sku)
              );
          CREATE REWRITE
              UPDATE 
              USING (SELECT
                  default::Product
              FILTER
                  (.sku = __subject__.sku)
              );
      };
  };
  ALTER TYPE default::Product {
      CREATE MULTI LINK batches := (.<product[IS default::Batch]);
  };
};
