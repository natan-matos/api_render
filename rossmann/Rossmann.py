import pickle
import inflection
import pandas as pd
import numpy as np
import math
import datetime

class Rossmann( object ):
    def __init__(self):
        self.home_path = ''
        self.competition_distance = pickle.load(open(self.home_path + 'parameters/competition_distance_scaler.pkl', 'rb'))
        self.competition_time = pickle.load(open(self.home_path + 'parameters/competition_time_month_scaler.pkl', 'rb'))
        self.promo_time = pickle.load(open(self.home_path + 'parameters/promo_time_week.pkl', 'rb'))
        self.store_type_label = pickle.load(open(self.home_path + 'parameters/store_type_label_encoder.pkl', 'rb'))
        self.year_scaler = pickle.load(open(self.home_path + 'parameters/year_scaler.pkl', 'rb'))
    
    def data_cleaning( self, df1):

        # Rename Columns
        cols_old = ['Store', 'DayOfWeek', 'Date', 'Open', 'Promo',
            'StateHoliday', 'SchoolHoliday', 'StoreType', 'Assortment',
            'CompetitionDistance', 'CompetitionOpenSinceMonth',
            'CompetitionOpenSinceYear', 'Promo2', 'Promo2SinceWeek',
            'Promo2SinceYear', 'PromoInterval']
        snakecase = lambda x: inflection.underscore( x )
        cols_new = list( map( snakecase, cols_old ) )
        # Rename
        df1.columns = cols_new

        # Convert date type
        df1['date'] = pd.to_datetime( df1['date'] )

        # FILL OUT NAs
          #competition_distance       
        df1['competition_distance'] = df1['competition_distance'].apply(
            lambda x: 200000.0 if math.isnan( x ) else x
        )
        #competition_open_since_month 
        df1['competition_open_since_month'] = df1.apply(
                                                    lambda x: x['date'].month if math.isnan( x['competition_open_since_month'] ) else x['competition_open_since_month'], axis=1
                                                    )
        #competition_open_since_year
        df1['competition_open_since_year'] = df1.apply(
                                                    lambda x: x['date'].year if math.isnan( x['competition_open_since_year'] ) else x['competition_open_since_year'], axis=1
                                                    )
        #promo2_since_week 
        df1['promo2_since_week'] = df1.apply( 
                                            lambda x: x['date'].week if math.isnan( x['promo2_since_week'] ) else x['promo2_since_week'], axis=1
                                                    )
        #promo2_since_week 
        df1['promo2_since_week'] = df1.apply( 
                                            lambda x: x['date'].week if math.isnan( x['promo2_since_week'] ) else x['promo2_since_week'], axis=1
                                                    )
        #promo2_since_year 
        df1['promo2_since_year'] = df1.apply(lambda x: x['date'].year if math.isnan(x['promo2_since_year']) else x['promo2_since_year'], axis=1)

        # Change astype
        df1['competition_open_since_month'] = df1['competition_open_since_month'].astype( np.int64 )
        df1['competition_open_since_year'] = df1['competition_open_since_year'].astype( np.int64 )
        df1['promo2_since_week'] = df1['promo2_since_week'].astype( np.int64 )
        df1['promo2_since_year'] = df1['promo2_since_year'].astype( np.int64 )

        # promo_interval
        df1['promo_interval'].fillna(0, inplace=True)
        map_month = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7:'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        df1['month_map'] = df1['date'].dt.month.map( map_month )
        df1['is_promo'] = df1[['promo_interval', 'month_map']].apply(lambda x: 0 if x['promo_interval'] == 0 else 1 if x['month_map'] in x['promo_interval'].split(',') else 0, axis=1)

        return df1
    
    def feature_engineering(self, df2):

        ## 
        # year
        df2['year'] = df2['date'].dt.year

        # month
        df2['month'] = df2['date'].dt.month

        # day
        df2['day'] = df2['date'].dt.day

        # week of year
        df2['week_of_year'] = df2['date'].dt.isocalendar().week.astype(np.int64)

        # year week
        df2['year_week'] = df2['date'].dt.strftime( '%Y-%W' )

        # competition since
        df2['competition_since'] = df2.apply( lambda x: datetime.datetime(year=x['competition_open_since_year'],month=x['competition_open_since_month'],day=1 ), axis=1 )
        df2['competition_time_month'] = ( ( df2['date'] - df2['competition_since'] )/30).apply( lambda x: x.days ).astype( int )

        # promo since
        df2['promo_since'] = df2['promo2_since_year'].astype( str ) + '-' + df2['promo2_since_week'].astype( str )
        df2['promo_since'] = df2['promo_since'].apply( lambda x: datetime.datetime.strptime( x + '-1', '%Y-%W-%w' ) - datetime.timedelta( days=7 ) )
        df2['promo_time_week'] = ( ( df2['date'] - df2['promo_since'] )/7 ).apply(lambda x: x.days ).astype( int )

        # assortment
        df2['assortment'] = df2['assortment'].apply( lambda x: 'basic' if x == 'a' else 'extra' if x == 'b' else 'extended' )

        # state holiday
        df2['state_holiday'] = df2['state_holiday'].apply( lambda x: 'public_holiday' if x == 'a' else 'easter_holiday' if x == 'b' else 'christmas' if x == 'c' else 'regular_day' )

        ## Feature Filter
        
        # Filter columns
        drop_cols = [ 'open', 'promo_interval', 'month_map']
        df2 = df2.drop(drop_cols, axis=1)

        return df2

    def data_preparation(self, df5):
        df5['competition_time_month'] = df5['competition_time_month'].astype(np.int64)
        df5['promo_time_week'] = df5['promo_time_week'].astype(np.int64)

        ## Rescaling
        # competition distance
        df5['competition_distance'] = self.competition_time.fit_transform(df5[['competition_distance']].to_numpy())
        # year
        df5['year'] = self.year_scaler.fit_transform(df5[['year']].to_numpy())
        # competition time month
        df5['competition_time_month'] = self.competition_time.fit_transform(df5[['competition_time_month']].to_numpy())
        # promo time week
        df5['promo_time_week'] = self.promo_time.fit_transform(df5[['promo_time_week']].to_numpy())

        ## Enconding
        # state holiday
        df5 = pd.get_dummies( df5, prefix=['state_holiday'], columns=['state_holiday'])

        # store type      
        df5['store_type'] = self.store_type_label.fit_transform(df5['store_type'])

        # assortment
        assortment_dic = {'basic': 1,
                        'extra': 2,
                        'extended': 3}
        df5['assortment'] = df5['assortment'].map(assortment_dic)

        ## Data Nature Transformation

               
        # day of week
        df5['day_of_week_sin'] = df5['day_of_week'].apply(lambda x: np.sin(2 * np.pi * x / 7 ))
        df5['day_of_week_cos'] = df5['day_of_week'].apply(lambda x: np.cos(2 * np.pi * x / 7 ))

        # month
        df5['month_sin'] = df5['month'].apply(lambda x: np.sin(2 * np.pi * x / 12 ))
        df5['month_cos'] = df5['month'].apply(lambda x: np.cos(2 * np.pi * x / 12 ))

        # day
        df5['day_sin'] = df5['day'].apply(lambda x: np.sin(2 * np.pi * x / 31 ))
        df5['day_cos'] = df5['day'].apply(lambda x: np.cos(2 * np.pi * x / 31 ))

        # week of year
        df5['week_of_year_sin'] = df5['week_of_year'].apply(lambda x: np.sin(2 * np.pi * x / 52 ))
        df5['week_of_year_cos'] = df5['week_of_year'].apply(lambda x: np.cos(2 * np.pi * x / 52 ))

        ## Feature Selection
        # Manual Feature Selection

        cols_selected = [
        'store',
        'promo',
        'store_type',
        'assortment',
        'competition_distance',
        'competition_open_since_month',
        'competition_open_since_year',
        'promo2',
        'promo2_since_week',
        'promo2_since_year',
        'competition_time_month',
        'promo_time_week',
        'day_of_week_sin',
        'day_of_week_cos',
        'month_sin',
        'month_cos',
        'day_sin',
        'day_cos',
        'week_of_year_sin',
        'week_of_year_cos'
        ]

        return df5[ cols_selected ]
    
    def get_prediction(self, model, original_data, test_data):
        # prediction
        pred = model.predict( test_data )

        # join pred into the original data
        original_data['prediction'] = np.expm1(pred)

        return original_data.to_json(orient='records',date_format='iso')
