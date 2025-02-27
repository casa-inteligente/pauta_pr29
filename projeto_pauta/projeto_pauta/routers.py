class NovoBancoRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'resenha_livro':
            return 'resenha_livro'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'resenha_livro':
            return 'resenha_livro'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'resenha_livro' or \
           obj2._meta.app_label == 'resenha_livro':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'resenha_livro':
            return db == 'resenha_livro'
        return None
