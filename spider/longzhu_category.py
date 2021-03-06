#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-12-28 00:28:13
# Project: longzhu_category

from pyspider.libs.base_handler import *
import re
import pymysql
from datetime import datetime


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
               'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'
        }
    }
    
    def __init__(self):
        try:
            self.connect = pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='zhudao', charset='utf8mb4')
            
        except Exception as e:
            print('Cannot Connect To Mysql!/n', e)
            raise e
        self.pattern_shortName = re.compile(r'.+?game/(\w+)$')

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://m.longzhu.com/i/game', callback=self.detail_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    @config(priority=2)
    def detail_page(self, response):
        results = []
        for item in response.doc('div.list-item').items():
            re_short_name = self.pattern_shortName.match(item.find('a').attr('href'))
            pic = item.find('img').attr('src')
            result = {
                'name': item.find('a').attr('title'),
                'short_name': (re_short_name.group(1) if re_short_name else ''),
                'pic': pic if (pic != 'http://m.longzhu.com/i/game') else '',
                'icon': None,
                'small_icon': None,
                'count': 0,
                'mb_url': item.find('a').attr('href'),
                'pc_url': 'http://longzhu.com/channels/' + (re_short_name.group(1) if re_short_name else ''),
                'platform_id': 5,
                
            }
            results.append(result)
        return {
            "url": response.url,
            "title": response.doc('title').text(),
            'results': results,
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
                cursor.execute('select id from category where name=%s and platform_id=%s', (item['name'],item['platform_id']))
                result = cursor.fetchone()
                if result:
                    # 更新操作
                    sql = '''update category set 
                        short_name=%s, 
                        pic=%s, 
                        count=%s,
                        mb_url=%s,
                        pc_url=%s,
                        update_time=%s
                        where name=%s and platform_id=%s'''
                    cursor.execute(sql, (item['short_name'], 
                                         item['pic'], 
                                         item['count'], 
                                         item['mb_url'], 
                                         item['pc_url'], 
                                         datetime.now(),
                                         item['name'], 
                                         item['platform_id']))
                else:
                    # 插入操作
                    sql = '''insert into category(name, pic, icon, small_icon, count, mb_url, pc_url, short_name, platform_id, created_time) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(sql, (item['name'], 
                                         item['pic'], 
                                         item['icon'], 
                                         item['small_icon'], 
                                         item['count'],
                                         item['mb_url'], 
                                         item['pc_url'], 
                                         item['short_name'], 
                                         item['platform_id'],
                                        datetime.now(),))
                self.connect.commit()

            except Exception as e:
                self.connect.rollback()
                raise e
