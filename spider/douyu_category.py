#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-12-19 23:21:33
# Project: douyu_category

from pyspider.libs.base_handler import *
import pymysql
from datetime import datetime


class Handler(BaseHandler):
    crawl_config = {
    }
    
    def __init__(self):
        self.platform_id = 1
        try:
            self.connect = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='zhudao', charset='utf8mb4')
            
        except Exception as e:
            print('Cannot Connect To Mysql!/n', e)
            raise e

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('https://m.douyu.com/category?type=', callback=self.detail_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
            "results": response.json['cate2Info']
        }

    def on_result(self,result):
        if not result:
            return
        self.save_data(**result)
        
    def save_data(self, **kw):

        if len(kw['results']) == 0:
            return

        for item in kw['results']:
            try:
                cursor = self.connect.cursor()
                cursor.execute('select id from category where short_name=%s and platform_id=%s', (item['shortName'], self.platform_id))
                result = cursor.fetchone()
                if result:
                    # 更新操作
                    sql = '''update category set 
                        name=%s, 
                        pic=%s, 
                        icon=%s, 
                        small_icon=%s,
                        count=%s,
                        mb_url=%s,
                        pc_url=%s,
                        cate_id=%s,
                        update_time=%s
                        where short_name=%s and platform_id=%s'''
                    cursor.execute(sql, (item['cate2Name'], 
                                         item['pic'], 
                                         item['icon'], 
                                         item['smallIcon'], 
                                         item['count'], 
                                         'https://m.douyu.com/roomlists/' + item['shortName'], 
                                         'https://www.douyu.com/directory/game/' + item['shortName'],  
                                         item['cate2Id'], 
                                         datetime.now(),
                                         item['shortName'], 
                                         self.platform_id))
                else:
                    # 插入操作
                    sql = '''insert into category(name, pic, icon, small_icon, count, mb_url, pc_url, cate_id, short_name, platform_id, created_time) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(sql, (item['cate2Name'], 
                                         item['pic'], 
                                         item['icon'], 
                                         item['smallIcon'], 
                                         item['count'],
                                         'https://m.douyu.com/roomlists/' + item['shortName'], 
                                         'https://www.douyu.com/directory/game/' + item['shortName'], 
                                         item['cate2Id'], 
                                         item['shortName'], 
                                         self.platform_id,
                                         datetime.now(),))
                self.connect.commit()

            except Exception as e:
                self.connect.rollback()
                raise e